"""Train native-scale external patches, then select on full images only."""
import argparse
import json
import os
from pathlib import Path
import sys
import numpy as np
from tools.ball_candidate_selection import write
from tools.ball_detector_data import safe_member
from tools.ball_transfer_training import summarize, accepted
from tools.ball_confidence_calibration import threshold_packets, select_threshold
from tools.metrica_data import external_output, sha256


def subset(coco, images):
    ids={r['id'] for r in images}
    known={r['id']:r for r in coco['images']}
    if len(ids)!=len(images) or any(known.get(r['id'])!=r for r in images):
        raise ValueError('Selected native images differ from references')
    return {**coco,'images':images,'annotations':[a for a in coco['annotations'] if a['image_id'] in ids]}


def run(data,native,initial,baseline,plan_path,out,trained_study=None):
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8',errors='backslashreplace')
    data,native=Path(data),Path(native)
    plan=json.loads(Path(plan_path).read_text())
    manifest=json.loads((data/'manifest.json').read_text())
    source=json.loads((native/'manifest.json').read_text())
    if any(r['provided_fixture_used'] for r in (plan,manifest,source)):
        raise ValueError('External data required')
    if manifest['plan_sha256']!=sha256(plan_path) or manifest['native_manifest_sha256']!=sha256(native/'manifest.json'):
        raise ValueError('Registered data changed')
    if sha256(initial)!=plan['initial_weights_sha256'] or sha256(baseline)!=plan['baseline_weights_sha256']:
        raise ValueError('Initialization changed')
    for rel,h in manifest['image_sha256'].items():
        if sha256(safe_member(data,rel))!=h:raise ValueError('Patch pixels changed')
    for split,h in manifest['annotation_sha256'].items():
        if sha256(data/split/'_annotations.coco.json')!=h:raise ValueError('Patch annotations changed')
    for split,key in [('train','train_games'),('valid','validation_games'),('test','fixed_recheck_games')]:
        if source['splits'][split]['games']!=plan[key]:raise ValueError('Game split changed')
        if sha256(native/split/'_annotations.coco.json')!=source['annotation_sha256'][split]:raise ValueError('Native annotations changed')
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parents[1]
    hashes={p:sha256(repo/p) for p in ('tools/ball_patch_training.py','tools/ball_confidence_calibration.py','tools/ball_transfer_training.py','development/vision_box_audit.py')}
    write(out/'before-training.json',{'plan':plan,'plan_sha256':sha256(plan_path),'source_hashes':hashes,'manifest_sha256':sha256(data/'manifest.json')})
    os.environ.update(WANDB_DISABLED='true',HF_HUB_DISABLE_TELEMETRY='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import torch
    from rfdetr import RFDETRNano
    from rfdetr.assets.coco_classes import COCO_CLASSES
    from sahi.models.roboflow import RoboflowDetectionModel
    from sahi.predict import get_sliced_prediction
    from PIL import Image
    from importlib.metadata import version
    write(out/'runtime.json',{p:version(p) for p in ('rfdetr','torch','numpy','sahi','pytorch-lightning')})
    torch.manual_seed(plan['seed']);np.random.seed(plan['seed'])
    if trained_study is None:
        detector=RFDETRNano(pretrain_weights=str(initial),num_classes=1,device='cuda',trust_checkpoint=False)
        detector.train(dataset_dir=str(data),output_dir=str(out/'training'),epochs=plan['epochs'],
            lr=plan['lr'],lr_encoder=plan['lr_encoder'],batch_size=plan['batch_size'],grad_accum_steps=plan['grad_accum_steps'],num_workers=0,
            seed=plan['seed'],multi_scale=False,expanded_scales=False,use_ema=False,run_test=False,
            tensorboard=False,wandb=False,mlflow=False,clearml=False,save_dataset_grids=False,
            amp_dtype='fp16',device='cuda',eval_backend='faster_coco_eval',class_names=['ball'])
        trained=out/'training/checkpoint_best_total.pth'
        del detector;torch.cuda.empty_cache()
    else:
        previous=Path(trained_study)
        before=json.loads((previous/'before-training.json').read_text())
        freeze=json.loads((previous/'model-freeze.json').read_text())
        trained=previous/'training/checkpoint_best_total.pth'
        if before['plan_sha256']!=sha256(plan_path) or before['manifest_sha256']!=sha256(data/'manifest.json'):
            raise ValueError('Previous training protocol differs')
        if sha256(trained)!=freeze['weights_sha256']['trained']:
            raise ValueError('Previously frozen checkpoint changed')
        write(out/'training-reuse.json',{'before_training_sha256':sha256(previous/'before-training.json'),
            'model_freeze_sha256':sha256(previous/'model-freeze.json'),'checkpoint_sha256':sha256(trained),
            'previous_evaluation_consumed':False,'reason':'Enforce preregistered GREEDYNMM/IOS against SAHI low-confidence auto-switch; training unchanged.'})
    if not trained.exists():raise ValueError('No selected checkpoint')
    weights={'baseline':sha256(baseline),'trained':sha256(trained)}
    write(out/'model-freeze.json',{'weights_sha256':weights,'before_full_frame_selection':True})
    receipts={r['file']:r['sha256'] for r in source['images']}
    results={};selected=None;prediction_hashes={}
    for split in ('valid','test'):
        images=manifest['selected_native_images'][split];packets={}
        for name in ('baseline','trained'):
            original=name=='baseline'
            if original:
                detector=RFDETRNano(pretrain_weights=str(baseline),device='cuda',trust_checkpoint=False)
            else:
                detector=RFDETRNano.from_checkpoint(str(trained),device='cuda',trust_checkpoint=False)
            mapping={str(k):v for k,v in COCO_CLASSES.items()} if original else {'0':'sports ball','1':'unused'}
            adapter=RoboflowDetectionModel(model=detector,confidence_threshold=.3 if original else plan['raw_threshold'],category_mapping=mapping,device='cuda')
            packets[name]=[]
            for i,r in enumerate(images):
                rel=split+'/'+r['file_name'];path=safe_member(native,rel)
                if sha256(path)!=receipts[rel]:raise ValueError('Evaluation pixels changed')
                with Image.open(path) as im:rgb=np.array(im.convert('RGB'))
                prediction=get_sliced_prediction(rgb,adapter,slice_height=512 if original else plan['tile_size'],
                    slice_width=768 if original else plan['tile_size'],overlap_height_ratio=plan['tile_overlap'],overlap_width_ratio=plan['tile_overlap'],
                    postprocess_type='GREEDYNMM',postprocess_match_metric='IOS',postprocess_match_threshold=.5,
                    postprocess_class_agnostic=False,perform_standard_pred=True,verbose=0,force_postprocess_type=True)
                boxes=[{'box_xyxy':p.bbox.to_xyxy(),'confidence':float(p.score.value)} for p in prediction.object_prediction_list if p.category.id==(37 if original else 0)]
                packets[name].append({'image_id':r['id'],'image_sha256':receipts[rel],'predictions':boxes})
                if i%10==0:print(f'{split} {name}: {i+1}/{len(images)}',flush=True)
            target=out/(split+'-'+name+'.json');write(target,packets[name]);prediction_hashes[target.name]=sha256(target)
            del adapter,detector;torch.cuda.empty_cache()
        write(out/(split+'-freeze.json'),{'predictions':dict(prediction_hashes),'before_scoring':True})
        coco=subset(json.loads((native/split/'_annotations.coco.json').read_text()),images)
        base=summarize(packets['baseline'],coco)
        if split=='valid':
            scores=[{'threshold':t,'score':summarize(threshold_packets(packets['trained'],t),coco)} for t in plan['thresholds']]
            selected=select_threshold(scores,base)
            write(out/'threshold-freeze.json',{'selected':selected,'scores':scores,'baseline':base,'before_recheck_inference':True})
            if selected is None:
                results[split]={'baseline':base,'selected':None,'accepted':False};break
        score=summarize(threshold_packets(packets['trained'],selected['threshold']),coco)
        results[split]={'baseline':base,'selected':score,'accepted':accepted(base,score)}
    if any(sha256(repo/p)!=h for p,h in hashes.items()):raise ValueError('Study source changed')
    report={'version':plan['version'],'provided_fixture_used':False,'selected_release':False,'independent_test':False,
        'threshold':selected['threshold'] if selected else None,'results':results,'weights_sha256':weights,
        'source_hashes':hashes,'prediction_hashes':prediction_hashes,'patch_counts':manifest['counts'],
        'accepted_for_extended_validation':len(results)==2 and all(r['accepted'] for r in results.values()),'limits':plan['limits']}
    write(out/'report.json',report);print(json.dumps(report,indent=2),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('data','native','initial','baseline','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='ball-patch-training-plan.json')
    p.add_argument('--trained-study',help='Reuse exact frozen training; recompute all evaluation predictions')
    a=p.parse_args();run(a.data,a.native,a.initial,a.baseline,a.plan,a.out,a.trained_study)
