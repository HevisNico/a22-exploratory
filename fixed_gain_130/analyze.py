"""Paired seed-level analysis for fixed-gain controls and held-out rate checks."""
import csv,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.stats import beta,binomtest
P=Path(__file__).resolve().parent
REFERENCE=P/'reference_campaign' if (P/'reference_campaign').exists() else P.parent/'experiment_coupure'
def interval(values):
    a=np.asarray(values,float);rng=np.random.default_rng(224130);means=a[rng.integers(0,len(a),(20000,len(a)))].mean(1)
    return [float(v) for v in np.quantile(means,[.025,.975])]
def group(rows):
    a=[r['recall'] for r in rows];k=sum(r['full_network_word'] for r in rows);n=len(rows);timing=[r['relative_rms'] for r in rows if r['relative_rms'] is not None]
    return {'n':n,'mean_recall':float(np.mean(a)),'mean_recall_CI95':interval(a),'min_recall':min(a),'max_recall':max(a),'complete_words':k,'complete_word_probability_exact_CI95':[0. if k==0 else float(beta.ppf(.025,k,n-k+1)),1. if k==n else float(beta.ppf(.975,k+1,n-k))],'mean_relative_rms':float(np.mean(timing)) if timing else None,'timing_seeds':len(timing),'ambiguous_events':sum(r['ambiguous'] for r in rows),'duplicate_events':sum(r['duplicates'] for r in rows),'order_violations':sum(r['order_violations'] for r in rows)}
def paired(a,b):
    a={r['seed']:r for r in a};b={r['seed']:r for r in b};seeds=sorted(a.keys()&b.keys());d=np.array([a[s]['recall']-b[s]['recall'] for s in seeds]);w=int(sum(d>0));l=int(sum(d<0))
    return {'n':len(d),'mean_difference':float(d.mean()),'CI95':interval(d),'wins':w,'ties':int(sum(d==0)),'losses':l,'sign_p_two_sided':float(binomtest(w,w+l,.5).pvalue) if w+l else 1.}
def training_record(x,rule,level,seed):
    cells=[c for l in x['training'] for c in l['cells']];z=np.array([c['state']['z'] for c in cells]);g=np.exp(z);b=np.array([c['state']['b'] for c in cells]);diag=np.array([c['diagnostic'] for c in cells]);tail=x['training'][-1]['tail128']
    return {'condition':rule,'level':level,'seed':seed,'mean_gain':float(g.mean()),'gain_cap_fraction':float(np.mean(g>=4-1e-10)),'mean_b':float(b.mean()),'b_cap_fraction':float(np.mean(b>=1.1-1e-10)),'training_tail128_recall':tail['recall'],'training_tail128_complete_word':tail['full_network_word'],'tail128_delta_z':float(diag[:,2].sum()),'tail128_delta_b':float(diag[:,3].sum())}
def run():
    rows=[];training=[];loaded={};checks=0;checkpoints=0;minquiet=math.inf;problems=[];hashes={}
    def consume(x,path,gap,reference=False):
        nonlocal checks,checkpoints,minquiet
        rule=x['rule'];seed=x['seed'];level=min(2,int(round(x['sigma']/.05))-1)
        if x['status']!='OK_POINT_NOT_CERTIFIED' or x['training_N']!=2048:problems.append([str(path),'metadata'])
        if x['training']:
            if len(x['training'])!=130:problems.append([str(path),'training depth'])
            for layer in x['training']:
                for c in layer['cells']:
                    state=c['state'];z=state['z'];b=state['b']
                    if state['phase']!=0:problems.append([str(path),'training not READY'])
                    if rule.startswith('fixed_') and any(v!=math.log(4) for v in z):problems.append([str(path),'gain changed'])
                    if rule in ['fixed_all','fixed_all_max_b']:
                        expected=.08 if rule=='fixed_all' else 1.1
                        if b!=expected or c['diagnostic'][0]!=0 or c['diagnostic'][2]!=0 or c['diagnostic'][3]!=0:problems.append([str(path),'fixed parameters changed'])
            training.append(training_record(x,rule,level,seed))
            checkpoint=path.with_suffix('.states')
            serialized=[[float(v) for v in line.split()] for line in checkpoint.read_text().splitlines()]
            expected_state=[[*c['state']['z'],c['state']['b'],c['state']['q'],c['state']['time'],c['state']['phase']] for layer in x['training'] for c in layer['cells']]
            checkpoints+=1
            if len(serialized)!=1560 or serialized!=expected_state:problems.append([str(path),'checkpoint serialization differs from JSON state'])
        for test in x['tests']:
            if test['level']!=level:continue
            checks+=1
            if len(test['layers'])!=130:problems.append([str(path),'test depth'])
            for layer in test['layers']:
                minquiet=min(minquiet,layer['minimum_quiet'])
                if test['frozen'] and (layer['delta_z']!=0 or layer['delta_b']!=0):problems.append([str(path),'frozen parameters changed'])
                if rule.startswith('fixed_') and layer['delta_z']!=0:problems.append([str(path),'fixed gain changed at test'])
                if rule in ['fixed_all','fixed_all_max_b'] and layer['delta_b']!=0:problems.append([str(path),'fixed b changed at test'])
            from collections import Counter
            found=complete=0
            for events in test['output_events']:
                labels=[v[1] for v in events];counts=Counter(labels);found+=sum(counts[1000000+i]==1 for i in range(test['pulses']));complete+=labels==list(range(1000000,1000000+test['pulses']))
            m=test['layers'][-1]['metric']
            if found!=m['found'] or complete!=m['complete_lanes']:problems.append([str(path),'independent output recount mismatch'])
            rows.append({'condition':rule,'level':level,'seed':seed,'base_test_gap':gap,'pulses':test['pulses'],'frozen':test['frozen'],'reference_campaign':reference,**m,'all_layer_delta_z':sum(l['delta_z'] for l in test['layers']),'all_layer_delta_b':sum(l['delta_b'] for l in test['layers'])})
    for path in sorted((P/'output').glob('*.json')):
        if path.name.startswith('progress_'):continue
        x=json.loads(path.read_text());gap=x['base_test_gap'];level=x['tests'][0]['level'];key=(x['rule'],level,x['seed'],gap)
        if key in loaded:problems.append([str(path),'duplicate dataset'])
        loaded[key]=True;consume(x,path,gap);hashes[str(path.relative_to(P))]=hashlib.sha256(path.read_bytes()).hexdigest()
    expected={(r,l,s,20) for r in ['fixed_all','fixed_all_max_b','fixed_gain'] for l in range(3) for s in range(20)}|{(r,l,s,8) for r in ['fixed_all','fixed_all_max_b','fixed_gain','normal','ungated'] for l in range(3) for s in range(20)}
    if set(loaded)!=expected:raise RuntimeError({'missing':sorted(expected-set(loaded)),'extra':sorted(set(loaded)-expected)})
    reference_hashes={}
    for rule in ['normal','ungated']:
        for l in range(3):
            for seed in range(20):
                path=REFERENCE/'output'/f'{rule}_{l}_{seed}.json';x=json.loads(path.read_text());consume(x,path,20,True);reference_hashes[str(path.relative_to(REFERENCE))]=hashlib.sha256(path.read_bytes()).hexdigest()
    assert not problems and minquiet>0,problems
    groups={}
    def select(rule,level,gap=20,frozen=True,count=128):return [r for r in rows if r['condition']==rule and r['level']==level and r['base_test_gap']==gap and r['frozen']==frozen and r['pulses']==count]
    for rule in ['normal','ungated','fixed_all','fixed_all_max_b','fixed_gain']:
        for level in range(3):
            for gap in [20,8]:
                for frozen in ([True] if rule in ['fixed_all','fixed_all_max_b'] else [False,True]):
                    for count in [24,128]:groups[f'{rule}_L{level}_gap{gap}_N{count}_{"frozen" if frozen else "active"}']=group(select(rule,level,gap,frozen,count))
    comparisons={}
    for gap in [20,8]:
        for level in range(3):
            for rule in ['fixed_all','fixed_all_max_b','fixed_gain','ungated']:comparisons[f'gap{gap}_L{level}_normal_minus_{rule}']=paired(select('normal',level,gap),select(rule,level,gap))
            comparisons[f'gap{gap}_L{level}_fixed_gain_active_minus_frozen']=paired(select('fixed_gain',level,gap,False),select('fixed_gain',level,gap,True))
    order=sorted([f'gap20_L{l}_normal_minus_fixed_all' for l in range(3)],key=lambda k:comparisons[k]['sign_p_two_sided']);previous=0.
    for rank,key in enumerate(order):previous=max(previous,min(1.,(3-rank)*comparisons[key]['sign_p_two_sided']));comparisons[key]['primary_Holm_3']=previous
    training_groups={}
    for rule in ['normal','ungated','fixed_all','fixed_all_max_b','fixed_gain']:
        for level in range(3):
            rr=[r for r in training if r['condition']==rule and r['level']==level];assert len(rr)==20
            training_groups[f'{rule}_L{level}']={'n':20,'prepared_tail128':sum(r['training_tail128_complete_word'] for r in rr),**{k:float(np.mean([r[k] for r in rr])) for k in ['mean_gain','gain_cap_fraction','mean_b','b_cap_fraction','training_tail128_recall','tail128_delta_z','tail128_delta_b']}}
    result={'protocol':json.loads((P/'PROTOCOL.json').read_text()),'new_datasets':len(loaded),'reference_datasets':120,'groups':groups,'paired':comparisons,'training':training_groups}
    (P/'summary.json').write_text(json.dumps(result,indent=2))
    for filename,data in [('results.csv',rows),('training.csv',training)]:
        with (P/filename).open('w') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    audit={'status':'PASS','new_datasets':len(loaded),'reference_datasets':120,'matched_test_instances_checked':checks,'checkpoint_files_checked':checkpoints,'independent_final_output_recounts':'all matched','fixed_gain_and_fixed_b_changes':'zero in every required phase','minimum_quiet_time':minquiet,'problems':problems}
    (P/'AUDIT.json').write_text(json.dumps(audit,indent=2))
    provenance={'new_output_sha256':hashes,'reference_output_sha256':reference_hashes,'sources_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in P.iterdir() if f.suffix in ['.py','.cpp','.json'] and f.name!='PROVENANCE.json'}}
    (P/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2));return result
if __name__=='__main__':
    x=run();print(json.dumps({'new_datasets':x['new_datasets'],'primary':{k:v for k,v in x['paired'].items() if k.startswith('gap20') and k.endswith('minus_fixed_all')}},indent=2))
