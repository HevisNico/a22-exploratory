import csv,json,math,collections
from pathlib import Path
import numpy as np
ROOT=Path(__file__).parent

def metrics(d,layer=None):
    case=d['case'];layer=layer or case.get('depth',18);n=len(d['source_probes']);dates=d['source_probes'];cells=[c for c in d['cells'] if c['layer']==layer]
    # A reference-active lane is defined by its first 24 separated probes in the
    # matching unperturbed topology, not by its survival in this realization.
    refname='baseline'
    name=case['name']
    if name.startswith('depth130'):refname='depth130_delay' if case.get('delay') else 'depth130'
    elif name.startswith(('ring','parents','random')):refname=name.split('_noisy_')[0]
    elif case.get('delay'):refname='baseline_delay'
    path=ROOT/'output'/(refname+'.json')
    if not path.exists():return None
    ref=json.loads(path.read_text())
    if ref['status']!='OK_POINT_NOT_CERTIFIED':return None
    rcells=[c for c in ref['cells'] if c['layer']==layer]
    active={c['lane'] for c in rcells if len(c['events'])==n and {l for t,l in c['events']}==set(range(128,128+n))}
    reachable={0}
    for grow in d['graph'][:layer]:reachable={j for j,ps in enumerate(grow) if any(p in reachable for p in ps)}
    actual_complete=sum(len(c['events'])==n and {l for t,l in c['events']}==set(range(128,128+n)) for c in cells)
    expected=len(active)*n;found=0;perfect=0;total=0;ambiguous=0;duplicates=0;rel=[];abs_err=[];lastrel=[];meanlat=[];latstd=[]
    for c in cells:
        ev=collections.defaultdict(list)
        for t,l in c['events']:
            total+=1
            if l is None:ambiguous+=1
            else:ev[l].append(t)
        duplicates+=sum(max(0,len(ts)-1) for ts in ev.values())
        if c['lane'] not in active:continue
        found+=sum(len(ev[128+i])==1 for i in range(n))
        good=all(len(ev[128+i])==1 for i in range(n)) and len(c['events'])==n
        perfect+=good
        lats=[ev[128+i][0]-dates[i] for i in range(n) if len(ev[128+i])==1]
        if lats:meanlat.append(float(np.mean(lats)));latstd.append(float(np.std(lats)))
        for i in range(n-1):
            if len(ev[128+i])==len(ev[129+i])==1:
                delta=(ev[129+i][0]-ev[128+i][0])-(dates[i+1]-dates[i]);abs_err.append(delta);rel.append(delta/(dates[i+1]-dates[i]))
                if i>=n//2:lastrel.append(delta/(dates[i+1]-dates[i]))
    return {'active_reference_lanes':len(active),'reachable_lanes':len(reachable),'complete_word_lanes':actual_complete,'expected':expected,'found':found,'recall':found/expected if expected else None,'events':total,'ambiguous':ambiguous,'duplicates':duplicates,'perfect_word_fraction':perfect/len(active) if active else None,'interval_pairs':len(rel),'interval_rms':float(np.sqrt(np.mean(np.array(abs_err)**2))) if rel else None,'relative_rms':float(np.sqrt(np.mean(np.array(rel)**2))) if rel else None,'late_relative_rms':float(np.sqrt(np.mean(np.array(lastrel)**2))) if lastrel else None,'max_interval_error':max(map(abs,abs_err),default=None),'mean_latency':float(np.mean(meanlat)) if meanlat else None,'mean_latency_std':float(np.mean(latstd)) if latstd else None,'gain_moves':sum(c['probe_gain_moves'] for c in cells)}

def main():
    rows=[];errors=[]
    for path in sorted((ROOT/'output').glob('*.json')):
        d=json.loads(path.read_text())
        if d['status']!='OK_POINT_NOT_CERTIFIED':errors.append({'name':d['case']['name'],'error':d.get('error'),'layer':d.get('layer'),'lane':d.get('lane')});continue
        m=metrics(d)
        if m:rows.append({'name':d['case']['name'],**d['case'],**m,'seconds':d['seconds']})
    (ROOT/'summary.json').write_text(json.dumps({'runs':rows,'unsupported':errors},indent=2))
    if rows:
        fields=list(dict.fromkeys(k for row in rows for k in row))
        with (ROOT/'summary.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    print('successful',len(rows),'unsupported',len(errors))
    for prefix in ['baseline','amp_','jitter_','q_','joint_','allnoise_','gap_','shape_','width_','depth130','ring','parents','random']:
        groups=collections.defaultdict(list)
        for row in rows:
            if row['name'].startswith(prefix):
                key=row['name'].rsplit('_',1)[0] if prefix in ['amp_','jitter_','q_','joint_','allnoise_'] else row['name']
                groups[key].append(row)
        for key,rs in groups.items():
            def average(field):
                vv=[r[field] for r in rs if r[field] is not None]
                return float(np.mean(vv)) if vv else None
            print(key,'N',len(rs),'active',rs[0]['active_reference_lanes'],'recall',average('recall'),'relRMS',average('relative_rms'),'word',average('perfect_word_fraction'))
    print('ERRORS',errors)
if __name__=='__main__':main()
