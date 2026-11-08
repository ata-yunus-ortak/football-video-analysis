"""Validation-only operating-threshold selection for a frozen external model."""
import argparse
import json
import os
from pathlib import Path
import numpy as np
from tools.ball_candidate_selection import write
from tools.ball_detector_data import safe_member
from tools.ball_transfer_training import summarize, accepted
from tools.metrica_data import external_output, sha256


def threshold_packets(packets, threshold):
    if not np.isfinite(threshold) or not 0 < threshold <= 1:
        raise ValueError('Finite confidence threshold in (0,1] required')
    return [{**p,'predictions':[r for r in p['predictions'] if r['confidence']>=threshold]} for p in packets]


def select_threshold(scores, baseline):
    choices=[r for r in scores if r['score']['matched']>=baseline['matched']]
    if not choices or baseline['matched']<=0:return None
    return min(choices,key=lambda r:(r['score']['unmatched_predictions'],-r['score']['matched'],-r['threshold']))


def run(data, study, plan_path, out):
    data,study=Path(data),Path(study);plan=json.loads(Path(plan_path).read_text())
    previous=json.loads((study/'report.json').read_text());manifest=json.loads((data/'manifest.json').read_text())
    if plan['provided_fixture_used'] or previous['provided_fixture_used'] or manifest['provided_fixture_used']:
        raise ValueError('External inputs required')
    if manifest['splits']['valid']['games']!=[plan['validation_game']] or manifest['splits']['test']['games']!=[plan['fixed_recheck_game']]:
        raise ValueError('Registered games differ')
    checkpoint=study/'training/checkpoint_best_total.pth'
    if sha256(checkpoint)!=plan['model_sha256'] or previous['weights_sha256']['trained']!=plan['model_sha256']:
        raise ValueError('Frozen model changed')
    prediction_freeze=json.loads((study/'prediction-freeze.json').read_text())
    if sha256(study/'prediction-freeze.json')!=previous['prediction_freeze_sha256']:
        raise ValueError('Baseline freeze changed')
    for split in ('valid','test'):
        p=study/('coco-'+split+'.jsonl')
        if sha256(p)!=prediction_freeze['files'][p.name]:raise ValueError('Baseline predictions changed')
        if sha256(data/split/'_annotations.coco.json')!=manifest['annotation_sha256'][split]:raise ValueError('Targets changed')
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    write(out/'before-inference.json',{'plan':plan,'source_sha256':sha256(__file__),
        'plan_sha256':sha256(plan_path),'previous_report_sha256':sha256(study/'report.json'),
        'manifest_sha256':sha256(data/'manifest.json')})
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    from rfdetr import RFDETRNano
    from PIL import Image
    detector=RFDETRNano.from_checkpoint(str(checkpoint),device='cuda',trust_checkpoint=False)
    results={};selected=None;raw_hashes={}
    for split in ('valid','test'):
        packets=[]
        receipts=[r for r in manifest['images'] if r['split']==split]
        for i,r in enumerate(receipts):
            path=safe_member(data,r['file'])
            if sha256(path)!=r['sha256']:raise ValueError('Pixels changed')
            with Image.open(path) as im:rgb=np.array(im.convert('RGB'))
            d=detector.predict(rgb,threshold=plan['raw_inference_threshold'])
            packets.append({'image_id':i+1,'file_name':path.name,'image_sha256':r['sha256'],
                'predictions':[{'box_xyxy':b.tolist(),'confidence':float(c)}
                               for b,c,k in zip(d.xyxy,d.confidence,d.class_id) if int(k)==0]})
        dest=out/(split+'-raw.json');write(dest,packets);raw_hashes[split]=sha256(dest)
        write(out/(split+'-freeze.json'),{'predictions_sha256':raw_hashes[split],'before_target_scoring':True})
        coco=json.loads((data/split/'_annotations.coco.json').read_text())
        if [p['file_name'] for p in packets]!=[r['file_name'] for r in coco['images']]:
            raise ValueError('Pixel/label correspondence differs')
        baseline=summarize([json.loads(s) for s in (study/('coco-'+split+'.jsonl')).read_text().splitlines()],coco)
        if split=='valid':
            scores=[{'threshold':t,'score':summarize(threshold_packets(packets,t),coco)} for t in plan['confidence_thresholds']]
            selected=select_threshold(scores,baseline)
            write(out/'threshold-freeze.json',{'selected':selected,'all_validation_scores':scores,
                'baseline':baseline,'before_recheck_inference':True})
            if selected is None:
                results[split]={'baseline':baseline,'selected':None};break
        score=summarize(threshold_packets(packets,selected['threshold']),coco)
        results[split]={'baseline':baseline,'selected':score,'accepted':accepted(baseline,score)}
        print(f'{split}: completed frozen-model calibration check',flush=True)
    report={'version':plan['version'],'threshold':selected['threshold'] if selected else None,
        'results':results,'accepted_for_extended_validation':len(results)==2 and all(r.get('accepted',False) for r in results.values()),
        'provided_fixture_used':False,'selected_release':False,'independent_test':False,
        'model_sha256':sha256(checkpoint),'model_changed':False,'raw_prediction_hashes':raw_hashes,
        'threshold_freeze_sha256':sha256(out/'threshold-freeze.json'),'source_sha256':sha256(__file__),
        'limits':plan['limits']}
    write(out/'report.json',report);print(json.dumps(report,indent=2),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('data','study','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='ball-confidence-calibration-plan.json')
    a=p.parse_args();run(a.data,a.study,a.plan,a.out)
