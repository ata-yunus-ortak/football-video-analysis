"""Acquire registered external development files, never reserved test data.

Resolve the public download redirect once, then fetch verified byte ranges.
Temporary signed URLs remain in memory; logs record only public source URLs.
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import time
import urllib.request
from tools.metrica_data import external_output, sha256, verify_file
from tools.fresh_check import fetch


def ranges(entry, target, workers):
    size = entry['bytes']; chunk = 4*1024*1024
    parts = target.parent/(target.name+'.transport')
    parts.mkdir(exist_ok=True)
    req = urllib.request.Request(entry['url']+'?download=true', headers={'Range':'bytes=0-0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        signed_url = response.geturl()
    jobs = [(i,a,min(a+chunk,size)-1) for i,a in enumerate(range(0,size,chunk))]

    def part(job):
        i,a,b = job; path = parts/f'{i:03d}.part'
        if path.exists() and path.stat().st_size == b-a+1: return
        for attempt in range(4):
            try:
                request = urllib.request.Request(signed_url, headers={'Range':f'bytes={a}-{b}'})
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.status != 206 or response.headers.get('Content-Range') != f'bytes {a}-{b}/{size}':
                        raise ValueError('Unexpected byte range')
                    data = response.read()
                if len(data) != b-a+1: raise ValueError('Incomplete byte range')
                path.write_bytes(data); return
            except Exception:
                if attempt == 3: raise RuntimeError(f'External range {i} failed') from None
                time.sleep(attempt+1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for count, _ in enumerate(pool.map(part,jobs),1):
            if count % 12 == 0:
                print(json.dumps({'file':target.name,'completed_parts':count,'total':len(jobs)}),flush=True)
    temporary = target.with_suffix(target.suffix+'.assembled')
    with temporary.open('wb') as stream:
        for i,a,b in jobs: stream.write((parts/f'{i:03d}.part').read_bytes())
    if sha256(temporary) != entry['sha256']: raise ValueError('Assembled source SHA256 mismatch')
    temporary.replace(target)


def run(plan_path, fixtures, out, workers=8):
    plan = json.loads(Path(plan_path).read_text())
    if (plan['repository'] != 'https://huggingface.co/datasets/pysport/idsse-data'
            or plan['provided_fixture_used'] is not False or not 1 <= workers <= 16):
        raise ValueError('Registered external download required')
    files = [e for e in plan['files'] if e['fixture_id'] in fixtures]
    if set(fixtures) != {e['fixture_id'] for e in files} or any(e['split']=='reserved_test' for e in files):
        raise ValueError('Only registered training/validation fixtures may be downloaded')
    for e in files:
        if Path(e['path']).name != e['path'] or e['url'] != plan['repository']+'/resolve/'+plan['commit']+'/'+e['path']:
            raise ValueError('Unexpected pinned source path')
    out = external_output(out); out.mkdir(parents=True, exist_ok=True)
    registration = out/'download-registration.json'
    current = {'plan_sha256':sha256(plan_path),'fixtures':fixtures,'files':files,
               'downloader_sha256':sha256(__file__),'provided_fixture_used':False}
    if registration.exists():
        if json.loads(registration.read_text()) != current: raise ValueError('Use a new output directory for another registration')
    else: registration.write_text(json.dumps(current,indent=2))
    records = {}
    for entry in files:
        path = out/entry['path']
        if path.exists():
            if path.stat().st_size != entry['bytes']: raise ValueError('Existing source size mismatch')
            if entry['sha256'] and sha256(path) != entry['sha256']: raise ValueError('Existing source SHA256 mismatch')
        elif entry['sha256']: ranges(entry,path,workers)
        else: fetch(entry['url'],path,size=entry['bytes'])
        if not entry['sha256']: verify_file(path,entry)
        records[path.name] = {'sha256':sha256(path),'bytes':path.stat().st_size,'url':entry['url']}
        (out/'download-manifest.json').write_text(json.dumps(records,indent=2))
        print(json.dumps({'verified_file':path.name,'bytes':path.stat().st_size}),flush=True)
    return records


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',default='sportec-data-plan.json')
    p.add_argument('--fixtures',nargs='+',required=True);p.add_argument('--out',required=True)
    p.add_argument('--workers',type=int,default=8);a=p.parse_args()
    run(a.plan,a.fixtures,a.out,a.workers)
