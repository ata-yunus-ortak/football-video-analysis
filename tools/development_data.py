"""Rebuild the registered external development set from pinned public LFS data."""
import argparse,json
from pathlib import Path
from .fresh_check import get,fetch,prepare

def run(registry,out):
    p=json.loads(Path(registry).read_text());out=Path(out);out.mkdir(parents=True,exist_ok=False);local={**p,'development_fixtures':{}}
    for mid,entry in p['development_fixtures'].items():
        base=f'https://raw.githubusercontent.com/SkillCorner/opendata/{p["commit"]}/data/matches/{mid}/{mid}'
        pointer=get(base+'_tracking_extrapolated.jsonl').decode();info=dict(line.split(' ',1) for line in pointer.splitlines())
        root=out/'raw'/mid;fetch(base+'_match.json',root/'match.json')
        media=f'https://media.githubusercontent.com/media/SkillCorner/opendata/{p["commit"]}/data/matches/{mid}/{mid}_tracking_extrapolated.jsonl'
        fetch(media,root/'tracking.jsonl',info['oid'].split(':')[1],int(info['size']))
        prepared=prepare(root/'match.json',root/'tracking.jsonl',out/'prepared'/mid)
        local['development_fixtures'][mid]={**entry,**prepared};print(json.dumps({'external_development_fixture_prepared':mid}),flush=True)
    (out/'local-plan.json').write_text(json.dumps(local,indent=2));return out/'local-plan.json'

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--registry',default='external-selection.json');a.add_argument('--out',required=True);x=a.parse_args();run(x.registry,x.out)
