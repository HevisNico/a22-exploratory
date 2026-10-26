"""Seed-level paired analysis; no pulse or lane treated as an independent replicate."""
import csv, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.stats import beta, binomtest
P=Path(__file__).resolve().parent
def interval(x):
    x=np.asarray(x,float);rng=np.random.default_rng(220130)
    means=x[rng.integers(0,len(x),(20000,len(x)))].mean(1)
    return [float(v) for v in np.quantile(means,[.025,.975])]
def binomial_interval(k,n):return [0. if k==0 else float(beta.ppf(.025,k,n-k+1)),1. if k==n else float(beta.ppf(.975,k+1,n-k))]
def group(rows):
    x=[r['recall'] for r in rows];k=sum(r['full_network_word'] for r in rows);rms=[r['relative_rms'] for r in rows if r['relative_rms'] is not None]
    return {'n':len(rows),'mean_recall':float(np.mean(x)),'min_recall':min(x),'max_recall':max(x),'mean_recall_CI95':interval(x),'full_words':k,'full_word_probability_exact_CI95':binomial_interval(k,len(rows)),'mean_relative_rms':float(np.mean(rms)) if rms else None,'seeds_with_timing_pairs':len(rms),'mean_complete_lanes':float(np.mean([r['complete_lanes'] for r in rows])),'ambiguous':sum(r['ambiguous'] for r in rows),'duplicates':sum(r['duplicates'] for r in rows),'order_violations':sum(r['order_violations'] for r in rows)}
def paired(a,b):
    a={r['seed']:r for r in a};b={r['seed']:r for r in b};seeds=sorted(a.keys()&b.keys());d=np.array([a[s]['recall']-b[s]['recall'] for s in seeds]);w=int(sum(d>0));l=int(sum(d<0))
    return {'n':len(d),'mean_delta':float(d.mean()),'CI95':interval(d),'wins':w,'ties':int(sum(d==0)),'losses':l,'sign_p_two_sided':float(binomtest(w,w+l,.5).pvalue) if w+l else 1.}
def run():
    rows=[];training=[];profiles=[];datasets={};errors=[]
    for f in sorted((P/'output').glob('*.json')):
        if f.name=='clean_training.json':continue
        try:x=json.loads(f.read_text())
        except json.JSONDecodeError:errors.append(f.name);continue
        if x.get('status')!='OK_POINT_NOT_CERTIFIED':errors.append(f.name);continue
        clean=f.stem.startswith('clean_test');parts=f.stem.split('_');level=int(parts[-2]);condition='clean' if clean else x['rule'];seed=x['seed']
        datasets[(condition,level,seed)]=x
        if not clean:
            cells=[c for l in x['training'] for c in l['cells']];deep=x['training'][-1]['cells'];diag=np.array([c['diagnostic'] for c in cells]);g=np.exp([c['state']['z'] for c in cells]);b=np.array([c['state']['b'] for c in cells]);dg=np.exp([c['state']['z'] for c in deep])
            training.append({'condition':condition,'level':level,'seed':seed,'prepared_tail128':x['training'][-1]['tail128']['full_network_word'],'tail128_recall':x['training'][-1]['tail128']['recall'],'mean_gain':float(g.mean()),'mean_b':float(b.mean()),'gain_cap_fraction':float(np.mean(g>=4.-1e-10)),'b_cap_fraction':float(np.mean(b>=1.1-1e-10)),'tail128_gain_moves':int(diag[:,1].sum()),'tail128_delta_z':float(diag[:,2].sum()),'tail128_delta_b':float(diag[:,3].sum()),'tail128_cells_with_gain_moves':int(sum(diag[:,1]>0)),'deep_mean_gain':float(dg.mean()),'deep_gain_cap_fraction':float(np.mean(dg>=4.-1e-10))})
        for t in x['tests']:
            # Cross-level clean runs were deliberately suppressed in release.
            if clean and t['level']!=level:continue
            row={'condition':condition,'training_level':level,'test_level':t['level'],'seed':seed,'pulses':t['pulses'],'frozen':t['frozen'],**t['layers'][-1]['metric'],'test_delta_z_all_layers':sum(l['delta_z'] for l in t['layers']),'test_delta_b_all_layers':sum(l['delta_b'] for l in t['layers']),'gain_updates_all_layers':sum(l['gain_updates'] for l in t['layers'])}
            rows.append(row)
            if t['level']==level:
                for l in t['layers']:profiles.append({'condition':condition,'level':level,'seed':seed,'pulses':t['pulses'],'frozen':t['frozen'],'layer':l['layer'],**l['metric']})
    expected={(c,l,s) for c in ['normal','ungated','clean'] for l in range(3) for s in range(20)}
    if set(datasets)!=expected:raise RuntimeError({'missing':sorted(expected-set(datasets)),'extra':sorted(set(datasets)-expected),'errors':errors})
    groups={};comparisons={}
    def select(c,l,n=128,f=False,testlevel=None):return [r for r in rows if r['condition']==c and r['training_level']==l and r['test_level']==(l if testlevel is None else testlevel) and r['pulses']==n and r['frozen']==f]
    for l in range(3):
        for c in ['normal','ungated','clean']:
            for n in [24,128]:
                for f in [False,True]:groups[f'{c}_L{l}_{n}_{"frozen" if f else "active"}']=group(select(c,l,n,f))
        for label,a,b in [('normal_minus_ungated','normal','ungated'),('normal_minus_clean','normal','clean')]:
            for n in [24,128]:
                for f in [False,True]:comparisons[f'L{l}_{label}_{n}_{"frozen" if f else "active"}']=paired(select(a,l,n,f),select(b,l,n,f))
        comparisons[f'L{l}_normal_active_minus_frozen_128']=paired(select('normal',l),select('normal',l,f=True))
    # Holm correction across the three predefined primary ablation tests.
    keys=[f'L{l}_normal_minus_ungated_128_active' for l in range(3)];order=sorted(keys,key=lambda k:comparisons[k]['sign_p_two_sided']);previous=0.
    for rank,k in enumerate(order):previous=max(previous,min(1.,(3-rank)*comparisons[k]['sign_p_two_sided']));comparisons[k]['sign_p_Holm_3']=previous
    transfer={f'train{a}_test{b}':group(select('normal',a,f=True,testlevel=b)) for a in range(3) for b in range(3)}
    training_groups={}
    for c in ['normal','ungated']:
        for l in range(3):
            rr=[r for r in training if r['condition']==c and r['level']==l]
            tg={'n':len(rr),'prepared_tail128':sum(r['prepared_tail128'] for r in rr)}
            for k in ['tail128_recall','mean_gain','mean_b','gain_cap_fraction','b_cap_fraction','tail128_gain_moves','tail128_delta_z','tail128_delta_b','tail128_cells_with_gain_moves','deep_mean_gain','deep_gain_cap_fraction']:
                tg[k]=float(np.mean([r[k] for r in rr]));tg[k+'_min']=min(r[k] for r in rr);tg[k+'_max']=max(r[k] for r in rr)
            training_groups[f'{c}_L{l}']=tg
    result={'protocol':json.loads((P/'PROTOCOL.json').read_text()),'completed_datasets':len(datasets),'groups':groups,'paired':comparisons,'training':training_groups,'frozen_transfer128':transfer,'errors':errors}
    (P/'summary.json').write_text(json.dumps(result,indent=2))
    for name,data in [('summary.csv',rows),('training.csv',training),('profiles.csv',profiles)]:
        with (P/name).open('w') as out:
            w=csv.DictWriter(out,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    prov={'inputs':{},'outputs':{},'source_files':{}}
    for f in (P.parent/'upload').glob('*.zip'):prov['inputs'][f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
    for f in (P/'output').glob('*'):prov['outputs'][f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
    for f in P.iterdir():
        if f.suffix in ['.py','.cpp','.json'] and f.name!='PROVENANCE.json':prov['source_files'][f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
    (P/'PROVENANCE.json').write_text(json.dumps(prov,indent=2))
    return result
if __name__=='__main__':
    x=run()
    print(json.dumps({'datasets':x['completed_datasets'],'primary':{k:v for k,v in x['paired'].items() if 'ungated_128_active' in k}},indent=2))
