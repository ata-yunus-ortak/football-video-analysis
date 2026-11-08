"""Bounded public archive metadata inventory; never download image members."""
import argparse
import json
from pathlib import Path
import urllib.request
import zipfile
from tools.soccernet_sample import RangeReader
from tools.vision_gallery_build import member_payload
from tools.ball_candidate_selection import write
from tools.ball_detector_data import safe_member
from tools.metrica_data import external_output,sha256


def selected_indices(n):
    if type(n) is not int or n<1:raise ValueError('Nonempty archive required')
    return sorted({0,n//3,2*n//3,n-1})


def run(plan_path,out):
    plan=json.loads(Path(plan_path).read_text())
    if plan['provided_fixture_used'] or plan['dataset']!='SoccerNet/SN-GSR-2024' or plan['archive']!='valid.zip':
        raise ValueError('Registered external validation archive metadata only')
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    write(out/'before-access.json',{'plan':plan,'plan_sha256':sha256(plan_path),'source_sha256':sha256(__file__)})
    url=f"https://huggingface.co/datasets/{plan['dataset']}/resolve/{plan['commit']}/{plan['archive']}"
    with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':'bytes=0-0'}),timeout=30) as response:
        if response.status!=206 or response.headers.get('Content-Range')!=f"bytes 0-0/{plan['archive_bytes']}" or len(response.read(2))!=1:
            raise ValueError('Exact range support required')
        signed=response.geturl()
    reader=RangeReader(signed,plan['archive_bytes'],plan['max_download_bytes']);records=[]
    try:
        with zipfile.ZipFile(reader) as archive:
            names=sorted(n for n in archive.namelist() if n.endswith('/Labels-GameState.json'))
            selected=[names[i] for i in selected_indices(len(names))]
            write(out/'selection-before-members.json',{'sequence_count':len(names),'members':selected})
            for name in selected:
                info=archive.getinfo(name)
                if info.file_size>50000000:raise ValueError('Oversized metadata')
                reader.seek(info.header_offset)
                raw=reader.read(min(info.compress_size+65566,plan['archive_bytes']-info.header_offset))
                payload=member_payload(info,raw);path=safe_member(out/'metadata',name)
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
                data=json.loads(payload);game=str(data['info']['game_id'])
                records.append({'sequence':name.split('/')[0],'game_id':game,'fps':data['info']['frame_rate'],
                    'frames':len(data['images']),'metadata_sha256':sha256(path),'zip_crc_verified':True,
                    'outside_known_development_games':game not in plan['known_development_games']})
        report={'version':plan['version'],'sequences':records,'provided_fixture_used':False,
            'image_members_downloaded':0,'downloaded_range_bytes':reader.downloaded+1,'archive_sha256_verified':False,
            'independent_test_certified':False,'labels_used_for_model_selection':False,'source_url':url}
        write(out/'report.json',report);print(json.dumps(report,indent=2));return report
    finally:write(out/'range-receipts.json',reader.requests)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',default='ball-new-games-inventory-plan.json');p.add_argument('--out',required=True)
    a=p.parse_args();run(a.plan,a.out)
