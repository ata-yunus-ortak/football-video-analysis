"""External-only head transfer, bounded fine-tuning and frozen comparison."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import numpy as np
from development.ball_head_transfer import transfer_array
from development.vision_box_audit import match_boxes
from tools.ball_candidate_selection import write
from tools.ball_detector_data import safe_member
from tools.metrica_data import external_output, sha256


def summarize(packets, coco):
    refs={r['id']:[] for r in coco['images']}
    for a in coco['annotations']:
        x,y,w,h=a['bbox'];refs[a['image_id']].append({'box_xyxy':[x,y,x+w,y+h]})
    if [p['image_id'] for p in packets] != [r['id'] for r in coco['images']]:
        raise ValueError('Image correspondence differs')
    matched=predicted=reference=0
    for packet in packets:
        target=refs[packet['image_id']];pred=packet['predictions']
        matched+=len(match_boxes(pred,target,.5)['matches']);predicted+=len(pred);reference+=len(target)
    return {'matched':matched,'predicted':predicted,'reference':reference,
            'unmatched_predictions':predicted-matched,
            'precision':matched/predicted if predicted else 0.,
            'recall':matched/reference if reference else 0.}


def accepted(base, candidate):
    return (base['matched']>0 and base['unmatched_predictions']>0
            and candidate['matched']>=base['matched']
            and candidate['unmatched_predictions']<=.8*base['unmatched_predictions'])


def run(data, initial, plan_path, out):
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8',errors='backslashreplace')
    data=Path(data);plan=json.loads(Path(plan_path).read_text());manifest=json.loads((data/'manifest.json').read_text())
    if plan['provided_fixture_used'] or manifest['provided_fixture_used'] or manifest['version']!=plan['source_dataset_version']:
        raise ValueError('Registered external data required')
    for split,key in [('train','train_games'),('valid','validation_games'),('test','fixed_recheck_games')]:
        if manifest['splits'][split]['games']!=plan[key]:raise ValueError('Game split differs')
        if sha256(data/split/'_annotations.coco.json')!=manifest['annotation_sha256'][split]:
            raise ValueError('Annotations changed')
    if sha256(initial)!=plan['initial_weights_sha256']:raise ValueError('Initialization changed')
    for r in manifest['images']:
        if r['split'] in ('train','valid') and sha256(safe_member(data,r['file']))!=r['sha256']:
            raise ValueError('Training/validation pixels changed')
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parents[1]
    source_hashes={p:sha256(repo/p) for p in ('tools/ball_transfer_training.py','development/ball_head_transfer.py','development/vision_box_audit.py')}
    write(out/'before-training.json',{'plan':plan,'plan_sha256':sha256(plan_path),
        'source_hashes':source_hashes,'manifest_sha256':sha256(data/'manifest.json')})
    os.environ.update(WANDB_DISABLED='true',HF_HUB_DISABLE_TELEMETRY='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import torch
    from rfdetr import RFDETRNano
    from rfdetr.utilities.io import _safe_torch_load
    from rfdetr.assets.coco_classes import COCO_CLASSES
    from PIL import Image
    from importlib.metadata import version
    write(out/'runtime.json',{p:version(p) for p in ('rfdetr','torch','torchvision','numpy','pytorch-lightning','torchmetrics')})
    torch.manual_seed(plan['seed']);np.random.seed(plan['seed'])
    if COCO_CLASSES[plan['source_coco_ball_id']]!='sports ball':raise ValueError('COCO ball identity differs')
    original=_safe_torch_load(initial,trust=False);state=dict(original['model']);heads=[]
    for key,value in state.items():
        if 'class_embed' in key and key.endswith(('.weight','.bias')):
            state[key]=torch.from_numpy(transfer_array(value.cpu().numpy(),plan['source_coco_ball_id'],plan['unused_logit_bias']))
            heads.append(key)
    if not heads:raise ValueError('No source classifier heads')
    args=copy.deepcopy(original['args']);args.num_classes=1;args.class_names=['ball']
    mapped=out/'transferred-initial.pth'
    torch.save({'model':state,'args':args,'class_names':['ball']},mapped)
    detector=RFDETRNano(pretrain_weights=str(mapped),num_classes=1,device='cuda',trust_checkpoint=False)
    loaded=detector.model.model.state_dict()
    if any(not torch.equal(loaded[k].cpu(),v) for k,v in state.items()):
        raise ValueError('Constructor changed the transferred initial state')
    write(out/'initialization-check.json',{'changed_head_keys':heads,'other_tensors_preserved':True,
        'constructor_exact_state_verified':True,'source_ball_id':37,'target_ball_id':0,'unused_id':1,
        'checkpoint_sha256':sha256(mapped)})
    del original,state,loaded
    detector.train(dataset_dir=str(data),output_dir=str(out/'training'),epochs=plan['epochs'],
        lr=plan['lr'],lr_encoder=plan['lr_encoder'],batch_size=1,grad_accum_steps=16,num_workers=0,
        seed=plan['seed'],multi_scale=False,expanded_scales=False,use_ema=False,run_test=False,
        tensorboard=False,wandb=False,mlflow=False,clearml=False,save_dataset_grids=False,
        amp_dtype='fp16',device='cuda',eval_backend='faster_coco_eval',class_names=['ball'])
    trained=out/'training/checkpoint_best_total.pth'
    if not trained.exists():raise ValueError('No selected checkpoint')
    frozen={'coco':{'path':str(initial),'sha256':sha256(initial),'ball_id':37},
            'transferred':{'path':str(mapped),'sha256':sha256(mapped),'ball_id':0},
            'trained':{'path':str(trained),'sha256':sha256(trained),'ball_id':0}}
    write(out/'model-freeze.json',{'models':frozen,'before_recheck_inference':True})
    del detector;torch.cuda.empty_cache()
    pred_hashes={}
    for name,spec in frozen.items():
        if name=='coco':
            detector=RFDETRNano(pretrain_weights=spec['path'],device='cuda',trust_checkpoint=False)
        elif name=='transferred':
            detector=RFDETRNano(pretrain_weights=spec['path'],num_classes=1,device='cuda',trust_checkpoint=False)
        else:
            detector=RFDETRNano.from_checkpoint(spec['path'],device='cuda',trust_checkpoint=False)
        for split in ('valid','test'):
            receipts=[r for r in manifest['images'] if r['split']==split]
            target=out/(name+'-'+split+'.jsonl')
            with target.open('w',encoding='utf-8',newline='\n') as stream:
                for i,r in enumerate(receipts):
                    path=safe_member(data,r['file'])
                    if sha256(path)!=r['sha256']:raise ValueError('Evaluation pixels changed')
                    with Image.open(path) as image:rgb=np.array(image.convert('RGB'))
                    detections=detector.predict(rgb,threshold=plan['threshold'])
                    predictions=[{'box_xyxy':b.tolist(),'confidence':float(c)}
                        for b,c,k in zip(detections.xyxy,detections.confidence,detections.class_id) if int(k)==spec['ball_id']]
                    stream.write(json.dumps({'image_id':i+1,'image_sha256':r['sha256'],'predictions':predictions})+'\n')
            pred_hashes[target.name]=sha256(target)
            print(f'{name}: {split} {len(receipts)} predictions frozen',flush=True)
        del detector;torch.cuda.empty_cache()
    write(out/'prediction-freeze.json',{'files':pred_hashes,'before_comparison_scoring':True})
    scores={}
    for split in ('valid','test'):
        coco=json.loads((data/split/'_annotations.coco.json').read_text())
        scores[split]={}
        for name in frozen:
            path=out/(name+'-'+split+'.jsonl')
            if sha256(path)!=pred_hashes[path.name]:raise ValueError('Prediction changed')
            scores[split][name]=summarize([json.loads(s) for s in path.read_text().splitlines()],coco)
    if any(sha256(repo/p)!=h for p,h in source_hashes.items()):raise ValueError('Source changed during study')
    result={'version':plan['version'],'scores':scores,
        'accepted_for_extended_validation':all(accepted(s['coco'],s['trained']) for s in scores.values()),
        'selected_release':False,'provided_fixture_used':False,'independent_test':False,
        'source_hashes':source_hashes,'weights_sha256':{k:v['sha256'] for k,v in frozen.items()},
        'prediction_freeze_sha256':sha256(out/'prediction-freeze.json'),'limits':plan['limits']}
    write(out/'report.json',result);print(json.dumps(result,indent=2),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('data','initial','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='ball-transfer-training-plan.json')
    a=p.parse_args();run(a.data,a.initial,a.plan,a.out)
