"""Export external ball crops with a reference-independent validation grid."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
from development.ball_patch_geometry import tile_windows,crop_boxes,positive_window
from tools.ball_candidate_selection import write
from tools.ball_detector_data import safe_member
from tools.metrica_data import external_output,sha256


def run(native,plan_path,out):
    from PIL import Image
    native=Path(native);plan=json.loads(Path(plan_path).read_text());manifest=json.loads((native/'manifest.json').read_text())
    if plan['provided_fixture_used'] or manifest['provided_fixture_used'] or manifest['version']!=plan['source_dataset_version']:
        raise ValueError('Registered expanded external images required')
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    write(out/'before-export.json',{'plan':plan,'plan_sha256':sha256(plan_path),
        'source_manifest_sha256':sha256(native/'manifest.json'),'source_sha256':sha256(__file__)})
    receipts={r['file']:r for r in manifest['images']};rng=np.random.default_rng(plan['seed'])
    selected={};image_hashes={};annotation_hashes={};counts={}
    for split,key in [('train','train_games'),('valid','validation_games'),('test','fixed_recheck_games')]:
        if manifest['splits'][split]['games']!=plan[key]:raise ValueError('Game split changed')
        path=native/split/'_annotations.coco.json'
        if sha256(path)!=manifest['annotation_sha256'][split]:raise ValueError('Native reference changed')
        coco=json.loads(path.read_text());by_id=defaultdict(list)
        for a in coco['annotations']:by_id[a['image_id']].append(a['bbox'])
        images=[r for r in coco['images'] if (int(Path(r['file_name']).stem.rsplit('_',1)[1])-1)%plan['source_frame_modulus']==0]
        selected[split]=images
        if split=='test':continue
        dst={'images':[],'annotations':[],'categories':[{'id':1,'name':'ball','supercategory':'object'}],
             'info':{'description':'External research patches; validation grid does not use target locations'}}
        negative_count=0
        for image in images:
            source=native/split/image['file_name'];spec=receipts[split+'/'+image['file_name']]
            if sha256(source)!=spec['sha256']:raise ValueError('Native pixels changed')
            boxes=by_id[image['id']]
            if not boxes:raise ValueError('Unknown ball cannot become a negative frame')
            grid=tile_windows(image['width'],image['height'],plan['tile_size'],plan['tile_overlap'])
            if split=='train':
                positives=positive_window(boxes[0],image['width'],image['height'],plan['tile_size'],rng)
                negatives=[w for w in grid if not crop_boxes(boxes,w)]
                if not negatives:raise ValueError('No verified reference-free training window')
                windows=[positives,negatives[int(rng.integers(len(negatives)))]]
            else:windows=grid
            with Image.open(source) as im:
                rgb=im.convert('RGB')
                if rgb.size!=(image['width'],image['height']):raise ValueError('Image dimensions differ')
                for j,window in enumerate(windows):
                    crop=rgb.crop(window);name=Path(image['file_name']).stem+f'_{j:03}.png'
                    target=out/split/name;target.parent.mkdir(parents=True,exist_ok=True);crop.save(target)
                    with Image.open(target) as check:
                        if check.convert('RGB').tobytes()!=crop.tobytes():raise ValueError('Crop pixels changed')
                    image_hashes[split+'/'+name]=sha256(target);new_id=len(dst['images'])+1
                    dst['images'].append({'id':new_id,'file_name':name,'width':plan['tile_size'],'height':plan['tile_size']})
                    local=crop_boxes(boxes,window);negative_count+=not local
                    for b in local:
                        dst['annotations'].append({'id':len(dst['annotations'])+1,'image_id':new_id,
                            'category_id':1,'bbox':b,'area':b[2]*b[3],'iscrowd':0})
        path=out/split/'_annotations.coco.json';write(path,dst);annotation_hashes[split]=sha256(path)
        counts[split]={'source_images':len(images),'patches':len(dst['images']),
                       'ball_boxes':len(dst['annotations']),'reference_free_patches':negative_count}
    report={'version':plan['version'],'provided_fixture_used':False,'plan_sha256':sha256(plan_path),
        'native_manifest_sha256':sha256(native/'manifest.json'),'selected_native_images':selected,
        'image_sha256':image_hashes,'annotation_sha256':annotation_hashes,'counts':counts}
    write(out/'manifest.json',report);print(json.dumps(counts),flush=True);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('native','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='ball-patch-training-plan.json')
    a=p.parse_args();run(a.native,a.plan,a.out)
