"""Audit raw outputs and estimate paired selectivity/true-recall differences."""
import collections,csv,json,math,pathlib
import numpy as np
from run import CONDITIONS,SCENARIOS
P=pathlib.Path(__file__).resolve().parent
def recount(events,true_count,probes):
    found=0;complete=0;reached=set();lane_hits=0;pure_false=mixed=unattributed=orders=0;interval_errors=[]
    inclusive_found=0;inclusive_complete=0;pure_false_ids=set()
    gaps=[20,22,21,24,20,23]
    for train in events:
        pure=collections.defaultdict(list);inclusive=collections.Counter();allids=collections.Counter();fp=set();last=-1;ordered=True;inclusive_last=-1;inclusive_ordered=True
        for t,label,ids in train:
            if not ids:unattributed+=1;continue
            assert ids==sorted(set(ids)) and all(0<=i<128+probes for i in ids)
            allids.update(i for i in ids if i<128);false={i-128 for i in ids if i>=128};fp|=false;reached|=false
            true_ids=[i for i in ids if i<128]
            if len(true_ids)==1:
                inclusive[true_ids[0]]+=1
                if true_ids[0]<inclusive_last:inclusive_ordered=False
                inclusive_last=true_ids[0]
            if false and not true_ids:pure_false_ids|=false
            pure_false+=bool(false) and not true_ids;mixed+=len(ids)>1
            if len(ids)==1 and ids[0]<128:
                i=ids[0];pure[i].append(t)
                if i<last:ordered=False;orders+=1
                last=i
        valid={i for i in range(true_count) if len(pure[i])==1 and allids[i]==1};found+=len(valid);complete+=bool(true_count) and len(valid)==true_count and ordered;lane_hits+=len(fp)
        inclusive_valid=sum(inclusive[i]==1 and allids[i]==1 for i in range(true_count));inclusive_found+=inclusive_valid;inclusive_complete+=bool(true_count) and inclusive_valid==true_count and inclusive_ordered
        for i in range(true_count-1):
            if i in valid and i+1 in valid:interval_errors.append((pure[i+1][0]-pure[i][0]-gaps[i%6])/gaps[i%6])
    return dict(true_found=found,true_expected=true_count*12,complete_lanes=complete,full_true_word=complete==12,false_reached=len(reached),probe_count=probes,false_lane_hits=lane_hits,events=sum(map(len,events)),pure_false_events=int(pure_false),mixed_events=int(mixed),unattributed_events=unattributed,order_errors=orders),interval_errors,dict(inclusive_true_recall=inclusive_found/(12*true_count) if true_count else None,inclusive_full_true_word=inclusive_complete==12 if true_count else None,pure_false_probe_reach=len(pure_false_ids)/probes if probes else None)
def main():
    audit=dict(errors=[],datasets=0,raw_output_recounts=0,max_energy_relative_residual=0.,minimum_E_bound=100.,minimum_sampled_E=100.,injection_brackets_checked=0,injection_bracket_violations=0,unattributed_events=0)
    rows=[];profiles=collections.defaultdict(list);probe_hashes={};audit['historical_clean_regressions']=0
    for f in sorted((P/'results').glob('*.json')):
        d=json.loads(f.read_text());s=d['score'];e=d['energy'];w=e['work_components'];c=d['condition'];scene=d['scenario'];l=d['level'];seed=d['seed'];n=0 if scene=='noise_only' else 128
        independent,errs,extras=recount(d['output_events'],n,s['probe_count'])
        old_names={'learned':'normal_frozen','uniform4':'uniform4_learned_b','ungated':'ungated_frozen'}
        if scene=='clean' and c in old_names:
            oldpath=P.parent/'energy_experiment/results'/f'L{l}_s{seed}_{old_names[c]}.json'
            if oldpath.exists():
                old=json.loads(oldpath.read_text());event_pairs=[[[e[0],e[1]] for e in lane] for lane in d['output_events']]
                if event_pairs!=old['output_events'] or abs(d['energy']['work_total']-old['energy']['work_total'])>1e-10*old['energy']['work_total']:audit['errors'].append([f.name,'historical clean regression'])
                audit['historical_clean_regressions']+=1
        if independent!=s:audit['errors'].append([f.name,'raw output score mismatch',independent,s])
        audit['raw_output_recounts']+=1;audit['datasets']+=1;audit['unattributed_events']+=s['unattributed_events']
        tests=[('work sum',sum(w.values())-e['work_total'],e['work_total']),('fast drain',w['main_fast']-.75*e['fires'],max(1,e['fires'])),('pump balance',e['pump_supplied']-e['work_total']-(e['sum_terminal_E']-100*e['cells']),e['work_total'])]
        tests += [(key,w[key]-mass*e['input_pulses'],max(1,e['input_pulses'])) for key,mass in [('aux_mark',.2),('aux_silent',.7),('aux_error',.075)]]
        for name,error,scale in tests:
            rel=abs(error)/max(1,scale);audit['max_energy_relative_residual']=max(audit['max_energy_relative_residual'],rel)
            if rel>1e-8 and abs(error)>1e-6:audit['errors'].append([f.name,name,error])
        if w['gain_learning']!=0 or w['b_learning']!=0:audit['errors'].append([f.name,'frozen plastic work'])
        injected_layer=1 if scene=='wrong_lane' else 7
        counts=[x['score']['false_reached'] for x in d['layers']]
        if any(y>x for x,y in zip(counts[injected_layer-1:],counts[injected_layer:])):audit['errors'].append([f.name,'provenance appeared downstream without injection'])
        if any(x['score']['unattributed_events'] for x in d['layers']):audit['errors'].append([f.name,'unattributed intermediate outputs'])
        if e['continuous_E_lower_bound']<=0:audit['errors'].append([f.name,'nonpositive reserve bound'])
        audit['minimum_E_bound']=min(audit['minimum_E_bound'],e['continuous_E_lower_bound']);audit['minimum_sampled_E']=min(audit['minimum_sampled_E'],e['min_E_at_events'])
        audit['injection_brackets_checked']+=d['injection_timing']['brackets_checked'];audit['injection_bracket_violations']+=d['injection_timing']['violations']
        key=(l,seed,scene);p=json.dumps(d['probes'],separators=(',',':'))
        if key in probe_hashes and p!=probe_hashes[key]:audit['errors'].append([f.name,'unpaired probes'])
        probe_hashes[key]=p
        r=dict(level=l,seed=seed,condition=c,scenario=scene,false_reach=s['false_reached']/s['probe_count'] if s['probe_count'] else None,true_recall=s['true_found']/s['true_expected'] if n else None,full_true_word=s['full_true_word'] if n else None,false_reached=s['false_reached'],probe_count=s['probe_count'],true_found=s['true_found'],true_expected=s['true_expected'],false_lane_fraction=s['false_lane_hits']/(12*s['probe_count']) if s['probe_count'] else None,pure_false_events=s['pure_false_events'],mixed_events=s['mixed_events'],work=e['work_total'],interval_rms=float(np.sqrt(np.mean(np.square(errs)))) if errs else None,max_interval_error=max(map(abs,errs)) if errs else None,continuous_E_bound=e['continuous_E_lower_bound'],**w)
        r.update(extras);rows.append(r);profiles[l,c,scene].append([v['score']['false_reached']/s['probe_count'] if s['probe_count'] else 0. for v in d['layers']])
    data={(r['level'],r['seed'],r['condition'],r['scenario']):r for r in rows}
    expected=[(-1,0)]+[(l,s) for l in range(3) for s in range(20)]
    missing=[(l,s,c,t) for l,s in expected for c in CONDITIONS for t in SCENARIOS if (l,s,c,t) not in data]
    if missing:audit['errors'].append(['missing datasets',missing])
    if audit['datasets']!=2562:audit['errors'].append(['dataset count',audit['datasets']])
    if audit['unattributed_events']:audit['errors'].append(['unattributed outputs',audit['unattributed_events']])
    if audit['injection_bracket_violations']:audit['errors'].append(['injection timing violations',audit['injection_bracket_violations']])
    (P/'AUDIT.json').write_text(json.dumps(audit,indent=2))
    if audit['errors']:raise RuntimeError(audit)
    for r in rows:
        clean=data[r['level'],r['seed'],r['condition'],'clean'];r['true_loss_vs_clean']=clean['true_recall']-r['true_recall'] if r['true_recall'] is not None else None
    with (P/'metrics.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    rng=np.random.default_rng(20261026);groups=[];paired=[]
    for l in [-1,0,1,2]:
        seeds=[0] if l==-1 else list(range(20));ix=rng.integers(len(seeds),size=(20000,len(seeds)))
        for scene in SCENARIOS:
            for c in CONDITIONS:
                rs=[data[l,s,c,scene] for s in seeds];g=dict(level=l,condition=c,scenario=scene,n=len(rs),full_true_words=sum(bool(r['full_true_word']) for r in rs) if scene!='noise_only' else None,total_probes=sum(r['probe_count'] for r in rs),false_reached_count=sum(r['false_reached'] for r in rs))
                for key in ['false_reach','true_recall','true_loss_vs_clean','false_lane_fraction','work','pure_false_events','mixed_events','interval_rms','max_interval_error','inclusive_true_recall','pure_false_probe_reach']:
                    v=np.array([r[key] for r in rs if r[key] is not None],dtype=float)
                    if len(v)==len(rs):g[key]=dict(mean=float(v.mean()),CI95=np.quantile(v[ix].mean(axis=1),[.025,.975]).tolist(),min=float(v.min()),max=float(v.max()))
                    else:g[key]=None
                groups.append(g)
            for c in CONDITIONS[1:]:
                a=[data[l,s,'learned',scene] for s in seeds];b=[data[l,s,c,scene] for s in seeds];p=dict(level=l,scenario=scene,comparator=c,n=len(seeds),direction='learned minus comparator')
                for key in ['false_reach','true_recall','true_loss_vs_clean','work','inclusive_true_recall','pure_false_probe_reach']:
                    if a[0][key] is None or b[0][key] is None:p[key]=None;continue
                    delta=np.array([x[key]-y[key] for x,y in zip(a,b)]);p[key]=dict(mean=float(delta.mean()),CI95=np.quantile(delta[ix].mean(axis=1),[.025,.975]).tolist())
                p['selective_advantage_rule_met']=bool(l>=0 and p['false_reach'] and p['true_recall'] and p['false_reach']['CI95'][1]<0 and p['true_recall']['CI95'][0]>-.001)
                paired.append(p)
    result=dict(groups=groups,paired=paired,layer_profiles=[dict(level=l,condition=c,scenario=t,mean_false_reach=np.mean(v,axis=0).tolist()) for (l,c,t),v in sorted(profiles.items())])
    (P/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(audit))
    for g in groups:
        if g['level']==1:print(g['condition'],g['scenario'],'false',g['false_reach']['mean'] if g['false_reach'] else None,'true',g['true_recall']['mean'] if g['true_recall'] else None,'words',g['full_true_words'])
if __name__=='__main__':main()
