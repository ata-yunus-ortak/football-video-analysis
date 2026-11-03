"""Public external downloads and post-freeze proxy check. No competition input."""
import argparse,concurrent.futures,csv,hashlib,json,time,urllib.request
from pathlib import Path
import numpy as np
from clean_model.select import digest,infer,load,score
from clean_model.decoder import DecoderConfig
from clean_model.metrics import measure

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Football-external-remediation'}),timeout=90) as r:return r.read()
def fetch(url,path,expected=None,size=None):
    path=Path(path)
    if path.exists():
        if expected and digest(path)!=expected:raise ValueError('Existing external download hash differs')
        return
    path.parent.mkdir(exist_ok=True,parents=True);tmp=path.with_suffix(path.suffix+'.part')
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Football-external-remediation'})
            with urllib.request.urlopen(req,timeout=90) as r,tmp.open('wb') as f:
                while chunk:=r.read(1024*1024):f.write(chunk)
            if size is not None and tmp.stat().st_size!=size:raise ValueError('External size mismatch')
            if expected and digest(tmp)!=expected:raise ValueError('External content hash differs')
            tmp.rename(path);return
        except Exception:
            if attempt==2:raise
            time.sleep(attempt+1)
def prepare(meta,raw,out):
    m=json.loads(Path(meta).read_text());roster=m['players'];teams=np.array([0 if p['team_id']==m['home_team']['id'] else 1 for p in roster],np.int8);slots={p['id']:i for i,p in enumerate(roster)};pitch=np.array([m['pitch_length'],m['pitch_width']])
    with Path(raw).open(encoding='utf-8') as f:n=sum(1 for _ in f)
    x={'players':np.full((n,len(teams),2),np.nan),'ball':np.full((n,2),np.nan),'ball_observed':np.zeros(n,bool),'player_detected':np.zeros((n,len(teams)),bool),
        'period':np.zeros(n,np.int8),'frame':np.arange(n),'teams':teams,'pitch':pitch,'fps':np.array(10.)};y=np.full(n,'X',dtype='<U1')
    with Path(raw).open(encoding='utf-8') as f:
        for i,line in enumerate(f):
            r=json.loads(line);assert r['frame']==i;x['period'][i]=r.get('period') or 0;b=r['ball_data']
            if b.get('x') is not None and b.get('y') is not None:x['ball'][i]=np.array([b['x'],b['y']])+pitch/2
            x['ball_observed'][i]=b.get('is_detected') is True and np.isfinite(x['ball'][i]).all()
            for p in r['player_data']:
                j=slots.get(p['player_id'])
                if j is None or p.get('x') is None or p.get('y') is None:continue
                x['players'][i,j]=np.array([p['x'],p['y']])+pitch/2;x['player_detected'][i,j]=p.get('is_detected') is True
            y[i]={'home team':'H','away team':'A'}.get((r.get('possession') or {}).get('group'),'X') if x['period'][i] in (1,2) else 'X'
    out.mkdir(exist_ok=True,parents=True);np.savez_compressed(out/'inputs.npz',**x);np.savez_compressed(out/'provider-targets.npz',labels=y)
    return {'folder':str(out),'inputs_sha256':digest(out/'inputs.npz'),'targets_sha256':digest(out/'provider-targets.npz')}
def run(plan_path,model_path,out):
    plan=json.loads(Path(plan_path).read_text());model=json.loads(Path(model_path).read_text());out=Path(out);out.mkdir(exist_ok=False,parents=True)
    current=Path(__file__).resolve().parents[1]/'clean_model'
    assert all(digest(current/name)==sha for name,sha in model['source_hashes'].items())
    before={'model_sha256':digest(model_path),'source_sha256':digest(__file__),'before_fresh_tracking_download':True,'fresh_ids':[g['id'] for g in plan['fresh_test_fixtures']]}
    (out/'before-access.json').write_text(json.dumps(before,indent=2));commit=plan['commit'];jobs=[];records={}
    for g in plan['fresh_test_fixtures']:
        mid=str(g['id']);base=f'data/matches/{mid}/{mid}';raw='https://raw.githubusercontent.com/SkillCorner/opendata/'+commit+'/'+base
        pointer=get(raw+'_tracking_extrapolated.jsonl').decode();fields=dict(line.split(' ',1) for line in pointer.splitlines());expected=fields['oid'].split(':')[1];size=int(fields['size'])
        url='https://media.githubusercontent.com/media/SkillCorner/opendata/'+commit+'/'+base+'_tracking_extrapolated.jsonl'
        jobs.extend([(raw+'_match.json',out/'raw'/mid/'match.json',None,None),(url,out/'raw'/mid/'tracking.jsonl',expected,size)])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetch,*job):job for job in jobs}
        for future in concurrent.futures.as_completed(futures):
            job=futures[future];future.result();records[str(job[1].relative_to(out))]={'url':job[0],'sha256':digest(job[1]),'bytes':job[1].stat().st_size};print(json.dumps({'external_file_downloaded':str(job[1].relative_to(out)),'bytes':job[1].stat().st_size}),flush=True)
    entries={};predictions={};base=DecoderConfig(**model['base_config_at_10fps']) if model['base_config_at_10fps'] else None
    for g in plan['fresh_test_fixtures']:
        mid=str(g['id']);entry=prepare(out/'raw'/mid/'match.json',out/'raw'/mid/'tracking.jsonl',out/'prepared'/mid);entries[mid]=entry
        with np.load(Path(entry['folder'])/'inputs.npz',allow_pickle=False) as z:x={k:z[k] for k in z.files}
        pred=infer(x,base,model['policy']);path=out/(mid+'-prediction.csv')
        with path.open('x',newline='',encoding='utf-8') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(['frame','label']);w.writerows(zip(x['frame'],pred))
        predictions[mid]={'path':str(path),'sha256':digest(path)};print(json.dumps({'fresh_prediction_frozen':mid}),flush=True)
    (out/'prediction-freeze.json').write_text(json.dumps({'model_sha256':digest(model_path),'predictions':predictions,'before_proxy_evaluation':True},indent=2))
    metrics=[];games=[]
    for mid,entry in entries.items():
        x,y=load(entry);pred=np.loadtxt(predictions[mid]['path'],delimiter=',',dtype=str,skiprows=1)[:,1];m=measure(y,pred,x['period']);metrics.append(m);games.append({'id':mid,'metrics':m})
    assert digest(model_path)==before['model_sha256'] and digest(__file__)==before['source_sha256']
    result={'games':games,'mean_proxy':score(metrics),'official_competition_score':False,'human_ground_truth':False,'model_changed_after_test':False,'provided_fixture_used':False}
    (out/'download-manifest.json').write_text(json.dumps(records,indent=2));(out/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--model',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.plan,a.model,a.out)
