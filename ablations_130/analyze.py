import collections,csv,json,math
from pathlib import Path
import numpy as np
from scipy.stats import beta
P=Path(__file__).parent
def metrics(d,n=130):
    cells=[c for c in d['cells'] if c['layer']==n];dates=d['source_probes'];N=len(dates)
    found=complete=total=extra=ambiguous=duplicates=0;err=[];lateerr=[];early=late=0
    for c in cells:
        by=collections.defaultdict(list)
        for t,l in c['probe_events']:
            total+=1
            if l is None:ambiguous+=1
            else:by[l].append(t)
        found+=sum(len(by[128+i])==1 for i in range(N))
        early+=sum(len(by[128+i])==1 for i in range(N//2))
        late+=sum(len(by[128+i])==1 for i in range(N//2,N))
        duplicates+=sum(max(0,len(v)-1) for v in by.values())
        extra+=sum(len(v) for k,v in by.items() if k<128 or k>=128+N)
        complete+=all(len(by[128+i])==1 for i in range(N)) and len(c['probe_events'])==N
        for i in range(N-1):
            if len(by[128+i])==len(by[129+i])==1:
                e=((by[129+i][0]-by[128+i][0])-(dates[i+1]-dates[i]))/(dates[i+1]-dates[i]);err.append(e)
                if i>=N//2:lateerr.append(e)
    return {'recall':found/(12*N),'found':found,'expected':12*N,'total_events':total,'complete_lanes':complete,'full_network_word':complete==12,'any_output':total>0,'ambiguous':ambiguous,'duplicates':duplicates,'outside_labels':extra,'relative_rms':float(np.sqrt(np.mean(np.array(err)**2))) if err else None,'late_relative_rms':float(np.sqrt(np.mean(np.array(lateerr)**2))) if lateerr else None,'pairs':len(err),'early_recall':early/(12*N/2),'late_recall':late/(12*N/2),'mean_gain_before':float(np.mean([g for c in cells for g in c['before']['g']])),'mean_b_before':float(np.mean([c['before']['b'] for c in cells])),'training_events':sum(c['training_count'] for c in cells),'probe_gain_moves':sum(c['probe_gain_moves'] for c in cells)}
def interval(success,n):
    return [float(beta.ppf(.025,success,n-success+1)) if success else 0.,float(beta.ppf(.975,success+1,n-success)) if success<n else 1.]
def main():
    rows=[];errors=[];bylayer={}
    for p in sorted((P/'output').glob('*.json')):
        d=json.loads(p.read_text());c=d['case']
        if d['status']!='OK_POINT_NOT_CERTIFIED':errors.append({'name':c['name'],'error':d['error'],'layer':d['layer']});continue
        m=metrics(d)
        m['first_zero_test_layer']=next((x['layer'] for x in d['layers'] if x['probe_count']==0),None)
        m['first_zero_training_layer']=next((x['layer'] for x in d['layers'] if x['training_count']==0),None)
        rows.append({**c,**m,'seconds':d['seconds']})
        bylayer[c['name']]=[{'layer':n,**metrics(d,n)} for n in range(1,131)]
    groups={}
    for prefix in ['all_normal_','all_none_','all_ungated_','probe_normal_','frozen_learned_']:
        rs=[r for r in rows if r['name'].startswith(prefix)];N=len(rs)
        if not N:continue
        succ=sum(r['full_network_word'] for r in rs);anyout=sum(r['any_output'] for r in rs)
        rng=np.random.default_rng(2026);v=np.array([r['recall'] for r in rs]);means=np.mean(rng.choice(v,size=(10000,N),replace=True),axis=1)
        timing=[r['relative_rms'] for r in rs if r['relative_rms'] is not None]
        groups[prefix.rstrip('_')]={'n':N,'mean_recall':float(v.mean()),'min_recall':float(v.min()),'max_recall':float(v.max()),'seed_bootstrap_mean_CI95':list(np.quantile(means,[.025,.975])),'full_network_word_seeds':succ,'full_word_probability_exact_CI95':interval(succ,N),'any_output_seeds':anyout,'any_output_probability_exact_CI95':interval(anyout,N),'mean_complete_lanes':float(np.mean([r['complete_lanes'] for r in rs])),'mean_relative_rms':float(np.mean(timing)) if timing else None,'timing_seeds':len(timing),'mean_training_events':float(np.mean([r['training_events'] for r in rs]))}
    paired={}
    by={r['name']:r for r in rows}
    for a,b in [('all_normal','probe_normal'),('all_normal','all_ungated'),('all_normal','all_none'),('all_normal','frozen_learned')]:
        pairs=[(by[f'{a}_{seed}']['recall'],by[f'{b}_{seed}']['recall']) for seed in range(20) if f'{a}_{seed}' in by and f'{b}_{seed}' in by]
        if pairs:
            delta=np.array([x-y for x,y in pairs]);rng=np.random.default_rng(2026);means=np.mean(rng.choice(delta,(10000,len(delta)),replace=True),axis=1)
            paired[f'{a}_minus_{b}']={'n':len(pairs),'mean_delta_recall':float(delta.mean()),'bootstrap_CI95':list(np.quantile(means,[.025,.975])),'wins':int(sum(delta>1e-12)),'ties':int(sum(abs(delta)<=1e-12)),'losses':int(sum(delta<-1e-12))}
    result={'runs':rows,'groups':groups,'paired':paired,'unsupported':errors}
    (P/'summary.json').write_text(json.dumps(result,indent=2));(P/'by_layer.json').write_text(json.dumps(bylayer,separators=(',',':')))
    if rows:
        fields=list(dict.fromkeys(k for r in rows for k in r))
        with (P/'summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps({'completed':len(rows),'groups':groups,'paired':paired,'unsupported':errors},indent=2))
    return result,bylayer
if __name__=='__main__':main()
