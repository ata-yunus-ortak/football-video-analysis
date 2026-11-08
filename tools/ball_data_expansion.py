"""Bounded sparse external training acquisition with one redirect resolution."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import urllib.request
import zipfile
from tools.ball_candidate_selection import write
from tools.ball_detector_data import safe_member
from tools.metrica_data import external_output, sha256
from tools.soccernet_sample import RangeReader
from tools.vision_gallery_build import member_payload


def frame_numbers(plan):
    a,b,s=(plan[k] for k in ('frame_start','frame_stop','frame_stride'))
    if any(type(v) is not int for v in (a,b,s)) or not 0<=a<b<=750 or s<1:
        raise ValueError('Bounded positive sparse source frame interval required')
    return list(range(a+1,b+1,s))


def run(plan_path,out):
    plan=json.loads(Path(plan_path).read_text())
    if plan['dataset']!='SoccerNet/SN-GSR-2024' or plan['archive']!='train.zip' or plan['provided_fixture_used']:
        raise ValueError('Registered public training archive only')
    numbers=frame_numbers(plan);out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    write(out/'before-access.json',{'plan':plan,'plan_sha256':sha256(plan_path),'source_sha256':sha256(__file__)})
    public=f"https://huggingface.co/datasets/{plan['dataset']}/resolve/{plan['commit']}/{plan['archive']}"
    # Signed redirect is kept in memory only; all public provenance uses the pinned URL.
    request=urllib.request.Request(public,headers={'Range':'bytes=0-0'})
    with urllib.request.urlopen(request,timeout=30) as response:
        if response.status!=206 or response.headers.get('Content-Range')!=f"bytes 0-0/{plan['archive_bytes']}":
            raise ValueError('Exact public byte-range support required')
        if len(response.read(2))!=1:raise ValueError('Unexpected probe size')
        signed=response.geturl()
    remote=RangeReader(signed,plan['archive_bytes'],plan['max_download_bytes'])
    receipts=[];clips=[];total=1
    try:
        with zipfile.ZipFile(remote) as archive:
            members={r.filename:r for r in archive.infolist()}
            sequences=sorted({n.split('/')[0] for n in members if '/img1/' in n and n.endswith('.jpg')})
            write(out/'sequence-inventory.json',{'sequences':sequences,'count':len(sequences)})
            indices=plan['sequence_indices']
            if len(set(indices))!=len(indices) or any(type(i) is not int or not 0<=i<len(sequences) for i in indices):
                raise ValueError(f'Invalid sequence indices for {len(sequences)} registered archive sequences')
            selection=[sequences[i] for i in indices]
            write(out/'selection-before-download.json',{'sequences':selection,'frame_numbers':numbers})
            total+=remote.downloaded;receipts.extend(remote.requests)
            for sequence in selection:
                sample=out/sequence/'sample-v2';sample.mkdir(parents=True)
                write(sample/'before-access.json',{'plan':plan,'plan_sha256':sha256(plan_path)})
                names=[sequence+'/Labels-GameState.json']+[f'{sequence}/img1/{n:06}.jpg' for n in numbers]
                sizes={n:min(members[n].compress_size+65566,plan['archive_bytes']-members[n].header_offset) for n in names}
                if total+sum(sizes.values())>plan['max_download_bytes']:raise ValueError('Registered transfer budget exceeded')
                def download(name):
                    info=members[name]
                    if info.file_size>50000000:raise ValueError('Oversized archive member')
                    target=safe_member(sample/'sample',name)
                    reader=RangeReader(signed,plan['archive_bytes'],55000000)
                    reader.seek(info.header_offset);raw=reader.read(sizes[name])
                    payload=member_payload(info,raw)
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
                    return {'member':name,'bytes':len(payload),'sha256':sha256(target),
                            'crc32':f'{info.CRC:08x}','zip_crc_verified':True},reader.requests
                records=[]
                with ThreadPoolExecutor(max_workers=8) as pool:
                    for record,ranges in pool.map(download,names):
                        records.append(record);receipts.extend(ranges)
                        total+=sum(r['end']-r['start']+1 for r in ranges)
                labels=json.loads(safe_member(sample/'sample',names[0]).read_text())
                if labels['info']['frame_rate']!=25:raise ValueError('Unexpected native source frame rate')
                game=str(labels['info']['game_id'])
                if game not in plan['allowed_game_ids']:raise ValueError('Unexpected source game')
                write(sample/'manifest.json',{'complete':True,'provided_fixture_used':False,
                    'acquired_files':records,'frame_numbers':numbers,'sparse':True,'source_fps':25,
                    'archive_fully_downloaded_or_sha256_verified':False})
                clips.append({'id':sequence,'study':str((out/sequence).resolve()),'source_game_id':game,
                              'frames':len(numbers),'sparse':True})
                print(f'{sequence}: game {game}, {len(numbers)} sparse frames verified',flush=True)
        write(out/'gallery.json',{'clips':clips,'provided_fixture_used':False,'sparse':True})
        report={'version':plan['version'],'complete':True,'clips':len(clips),
            'frames':sum(c['frames'] for c in clips),'by_game':{g:sum(c['frames'] for c in clips if c['source_game_id']==g) for g in plan['allowed_game_ids']},
            'downloaded_range_bytes':total,'provided_fixture_used':False,'independent_new_matches':False,
            'archive_sha256_verified':False,'limits':plan['limits']}
        write(out/'report.json',report);print(json.dumps(report),flush=True);return report
    finally:
        write(out/'range-receipts.json',receipts)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',default='ball-data-expansion-plan.json');p.add_argument('--out',required=True)
    a=p.parse_args();run(a.plan,a.out)
