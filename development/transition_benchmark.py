"""Step 2: external interval references with explicit coverage and provenance."""
import math


KINDS={'control_start','control_end','touch','pass','turnover','stop','restart'}


def validate_reference(doc,split_plan,allow_recheck=False):
    if doc.get('provided_fixture_used') is not False or doc.get('source_kind')!='permitted_external_video':
        raise ValueError('Permitted external reference only')
    if doc.get('reference_origin') not in ('external_human_review','external_provider_proxy'):
        raise ValueError('Independent reference origin required')
    groups=split_plan['splits'];sets=[set(v) for v in groups.values()]
    if any(a&b for i,a in enumerate(sets) for b in sets[:i]):raise ValueError('Match leakage across splits')
    split=doc['split']
    if str(doc['game_id']) not in groups[split]:raise ValueError('Wrong match split')
    if split=='recheck' and not allow_recheck:raise ValueError('Recheck locked until candidate freeze')
    h=doc['video_sha256']
    if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Content hash required')
    windows=doc['coverage_s']
    for i,(a,b) in enumerate(windows):
        if not all(math.isfinite(v) for v in (a,b)) or not 0<=a<b or (i and a<windows[i-1][1]):raise ValueError('Ordered nonoverlapping coverage')
    ids=set()
    for e in doc['events']:
        if e['id'] in ids:raise ValueError('Duplicate reference event')
        ids.add(e['id']);a,b=e['earliest_s'],e['latest_s']
        if e['kind'] not in KINDS or not all(math.isfinite(v) for v in (a,b)) or a>b or not any(x<=a<=b<=y for x,y in windows):
            raise ValueError('Event outside explicit evaluable coverage')
        if e.get('team') not in ('H','A',None):raise ValueError('Invalid team')
    return doc


def evaluate_events(predicted,reference,tolerance_s=.5):
    """Maximum-cardinality one-to-one matching; intervals do not imply exact times."""
    if not math.isfinite(tolerance_s) or tolerance_s<0:raise ValueError('Invalid tolerance')
    refs=reference['events'];windows=reference['coverage_s']
    selected=[];unscored=0
    for p in predicted:
        if p['kind'] not in KINDS or not math.isfinite(p['time_s']):raise ValueError('Invalid predicted event')
        if p.get('left_censored') or p.get('right_censored'):unscored+=1;continue
        if any(a<=p['time_s']<b for a,b in windows):selected.append(p)
        else:unscored+=1
    edges=[]
    for p in selected:
        choices=[]
        for j,r in enumerate(refs):
            if p['kind']!=r['kind'] or (r.get('team') is not None and p.get('team')!=r['team']):continue
            if r.get('owner_id') is not None and p.get('owner_id')!=r['owner_id']:continue
            distance=max(r['earliest_s']-p['time_s'],0,p['time_s']-r['latest_s'])
            if distance<=tolerance_s:choices.append((distance,j))
        edges.append([j for _,j in sorted(choices)])
    matched={}
    def augment(i,seen):
        for j in edges[i]:
            if j in seen:continue
            seen.add(j)
            if j not in matched or augment(matched[j],seen):matched[j]=i;return True
        return False
    for i in range(len(selected)):augment(i,set())
    tp=len(matched);n=len(selected);m=len(refs)
    return {'matched':tp,'missed':m-tp,'extra':n-tp,'unscored_predictions':unscored,
        'f1':2*tp/(n+m) if n+m else None,'reference_origin':reference['reference_origin'],
        'uncertain_reference_events':sum(r['earliest_s']!=r['latest_s'] for r in refs),
        'official_score':False}
