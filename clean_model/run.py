"""Frozen metadata/automatic-coordinate inference. No public labels or old outputs."""
import argparse,csv,hashlib,json,math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from .atd import load
from .decoder import DecoderConfig
from .select import infer,digest

def run(meta,raw,model,out):
    model_path=Path(model);frozen=json.loads(model_path.read_text());root=Path(__file__).parent
    for name,sha in frozen['source_hashes'].items():
        if digest(root/name)!=sha:raise ValueError('Frozen source changed: '+name)
    if frozen['provided_fixture_used_for_selection'] is not False:raise ValueError('Unverified selection provenance')
    tree=ET.parse(meta).getroot();fps=float(tree.findtext('.//FrameRate'));field=tree.find('.//FieldSize');pitch=[float(field.findtext('Width')),float(field.findtext('Height'))]
    with Path(raw).open(encoding='utf-8-sig') as f:frames=sum(1 for _ in f)
    x=load(meta,raw,frames,fps,pitch);cfg=frozen['base_config_at_10fps'];base=None
    if cfg is not None:
        scaled={**cfg}
        for key in ('confirmation_frames','gap_frames','hold_frames'):scaled[key]=int(math.ceil(cfg[key]*fps/frozen['training_fps']))
        base=DecoderConfig(**scaled)
    pred=infer(x,base,frozen['policy']);target=Path(out);target.mkdir(exist_ok=False,parents=True);csvpath=target/'submission.csv'
    with csvpath.open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['frame','label']);w.writerows(zip(x['frame'],pred))
    assert len(pred)==frames and set(pred).issubset(set('HADX'))
    result={'frames':frames,'fps':fps,'model_sha256':digest(model_path),'source_freeze_verified':True,'prediction_sha256':digest(csvpath),
        'input_metadata_sha256':digest(meta),'input_tracking_sha256':digest(raw),'public_reference_read':False,'manual_annotations_read':False,
        'label_counts':{v:int((pred==v).sum()) for v in ('H','A','D','X')},'output':str(csvpath)}
    (target/'inference.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--meta',required=True);p.add_argument('--tracking',required=True);p.add_argument('--model',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.meta,a.tracking,a.model,a.out)
