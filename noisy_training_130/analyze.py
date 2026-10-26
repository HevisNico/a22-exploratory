import collections,csv,json,re
from pathlib import Path
import numpy as np
from scipy.stats import beta
P=Path(__file__).parent
def exact_ci(k,n):return [0. if k==0 else float(beta.ppf(.025,k,n-k+1)),1. if k==n else float(beta.ppf(.975,k+1,n-k))]
def bootstrap(v):
    v=np.asarray(v);rng=np.random.default_rng(2027)
    return list(np.quantile(np.mean(rng.choice(v,(10000,len(v)),replace=True),axis=1),[.025,.975]))
def main():
    data=[];errors=[]
    for path in sorted((P/'output_native').glob('*.json')):
        if not (re.fullmatch(r'seed_\d+\.json',path.name) or re.fullmatch(r'quiet_\d+\.json',path.name) or re.fullmatch(r'matched_clean_\d+\.json',path.name)):continue
        d=json.loads(path.read_text())
        if d['status']!='OK_POINT_NOT_CERTIFIED':errors.append(d);continue
        data.append(d)
    rows=[];groups={};paired={}
    noisy=[d for d in data if not d['quiet'] and d.get('condition','noisy_training')=='noisy_training']
    prepared=sum(d['prepared_observed'] for d in noisy)
    for d in data:
        for t in d['tests']:
            metric=dict(t['layers'][-1]);expected=list(range(1000000,1000000+t['pulses']))
            final=[c for c in t['cells'] if c['layer']==130]
            counts=[collections.Counter(label for time,label in c['events']) for c in final]
            metric['missing_labels']=sum(sum(counter[label]==0 for label in expected) for counter in counts)
            metric['duplicated_labels']=sum(sum(counter[label]>1 for label in expected) for counter in counts)
            metric['complete_lanes']=sum([l for time,l in c['events']]==expected for c in final)
            metric['full_network_word']=metric['complete_lanes']==12
            metric['order_violations']=sum(any(b<=a for a,b in zip([l for time,l in c['events'] if l is not None],[l for time,l in c['events'] if l is not None][1:])) for c in final)
            rows.append({'name':d['name'],'seed':d['seed'],'quiet':d['quiet'],'condition':d.get('condition','noisy_training'),'training_N':d['training_N'],'prepared':d['prepared_observed'],'stage':t['stage'],'freeze':t['freeze'],'pulses':t['pulses'],**metric,'minimum_quiet_time':t['minimum_quiet_time']})
    for stage in ['primary','long']:
        for frozen in [False,True]:
            key=f'{stage}_'+('frozen' if frozen else 'adaptive');rs=[r for r in rows if not r['quiet'] and r['condition']=='noisy_training' and r['stage']==stage and r['freeze']==frozen]
            if not rs:continue
            n=len(rs);full=sum(r['full_network_word'] for r in rs);vv=[r['recall'] for r in rs];rr=[r['relative_rms'] for r in rs if r['relative_rms'] is not None]
            groups[key]={'n':n,'mean_recall':float(np.mean(vv)),'min_recall':min(vv),'max_recall':max(vv),'mean_recall_seed_bootstrap_CI95':bootstrap(vv),'full_network_word_seeds':full,'full_word_probability_exact_CI95':exact_ci(full,n),'mean_complete_lanes':float(np.mean([r['complete_lanes'] for r in rs])),'mean_relative_rms':float(np.mean(rr)) if rr else None,'ambiguous_events':sum(r['ambiguous'] for r in rs),'duplicate_events':sum(r['duplicates'] for r in rs),'missing_labels':sum(r['missing_labels'] for r in rs),'duplicated_labels':sum(r['duplicated_labels'] for r in rs)}
        aa={r['seed']:r for r in rows if not r['quiet'] and r['condition']=='noisy_training' and r['stage']==stage and not r['freeze']};bb={r['seed']:r for r in rows if not r['quiet'] and r['condition']=='noisy_training' and r['stage']==stage and r['freeze']}
        if aa and bb:
            delta=[aa[k]['recall']-bb[k]['recall'] for k in sorted(aa.keys() & bb.keys())]
            paired[stage+'_adaptive_minus_frozen']={'n':len(delta),'mean_recall_difference':float(np.mean(delta)),'seed_bootstrap_CI95':bootstrap(delta),'wins':sum(x>1e-12 for x in delta),'ties':sum(abs(x)<=1e-12 for x in delta),'losses':sum(x<-1e-12 for x in delta)}
    for stage in ['primary','long']:
        rs=[r for r in rows if r['condition']=='clean_training' and r['stage']==stage]
        if not rs:continue
        vv=[r['recall'] for r in rs];full=sum(r['full_network_word'] for r in rs);rr=[r['relative_rms'] for r in rs if r['relative_rms'] is not None]
        groups['clean_'+stage]={'n':len(rs),'mean_recall':float(np.mean(vv)),'min_recall':min(vv),'max_recall':max(vv),'mean_recall_seed_bootstrap_CI95':bootstrap(vv),'full_network_word_seeds':full,'full_word_probability_exact_CI95':exact_ci(full,len(rs)),'mean_complete_lanes':float(np.mean([r['complete_lanes'] for r in rs])),'mean_relative_rms':float(np.mean(rr)) if rr else None}
        aa={r['seed']:r for r in rows if not r['quiet'] and r['condition']=='noisy_training' and r['stage']==stage and not r['freeze']};bb={r['seed']:r for r in rs}
        shared=sorted(aa.keys() & bb.keys())
        if shared:
            delta=[aa[k]['recall']-bb[k]['recall'] for k in shared]
            paired[stage+'_noisy_minus_clean_training']={'n':len(delta),'mean_recall_difference':float(np.mean(delta)),'seed_bootstrap_CI95':bootstrap(delta),'wins':sum(x>1e-12 for x in delta),'ties':sum(abs(x)<=1e-12 for x in delta),'losses':sum(x<-1e-12 for x in delta)}
    oldpath=P/'comparison_128.json'
    if oldpath.exists():
        old=json.loads(oldpath.read_text());before={r['seed']:r for r in old['runs'] if r['name'].startswith('all_normal_')};after={r['seed']:r for r in rows if not r['quiet'] and r['condition']=='noisy_training' and r['stage']=='primary' and not r['freeze']}
        shared=sorted(before.keys() & after.keys())
        if shared:
            delta=[after[k]['recall']-before[k]['recall'] for k in shared]
            paired['long_training_minus_128']={'n':len(shared),'mean_recall_difference':float(np.mean(delta)),'seed_bootstrap_CI95':bootstrap(delta),'wins':sum(x>1e-12 for x in delta),'ties':sum(abs(x)<=1e-12 for x in delta),'losses':sum(x<-1e-12 for x in delta)}
    result={'completed_noisy_seeds':len(noisy),'prepared_seeds':prepared,'training_length_distribution':dict(collections.Counter(str(d['training_N']) for d in noisy)),'groups':groups,'paired':paired,'runs':rows,'unsupported':errors}
    (P/'summary.json').write_text(json.dumps(result,indent=2))
    if rows:
        fields=list(dict.fromkeys(k for row in rows for k in row))
        with (P/'summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps({k:v for k,v in result.items() if k not in ['runs','unsupported']},indent=2));print('errors',errors)
    return result,data
if __name__=='__main__':main()
