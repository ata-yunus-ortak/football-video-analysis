import argparse,csv,json
from pathlib import Path

def run(path,frames):
    count=0
    with Path(path).open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['frame','label']:raise ValueError('Expected frame,label header')
        for i,row in enumerate(reader):
            if int(row['frame'])!=i or row['label'] not in ('H','A','D','X'):raise ValueError('Frame or label invalid')
            count+=1
    if count!=frames:raise ValueError('Incomplete match file')
    print(json.dumps({'file_format_verified':True,'rows':count,'public_reference_used':False}));return count

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path');p.add_argument('--frames',type=int,required=True);a=p.parse_args();run(a.path,a.frames)
