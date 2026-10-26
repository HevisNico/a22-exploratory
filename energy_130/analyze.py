"""Audit existing outputs and compute paired, network-seed-level summaries."""
import collections,csv,hashlib,json,math,pathlib
import numpy as np
P=pathlib.Path(__file__).resolve().parent
COMP=['main_admission','main_fast','main_slow','aux_admission','aux_mark','aux_silent','aux_error','gain_learning','b_learning']

def main():
    rows=[];data={};audit={'errors':[],'dataset_count':0,'matched_checkpoint_pairs':0,'max_section_relative_error':0.,'max_pump_balance_absolute_error':0.,'minimum_continuous_E_bound':100.,'minimum_sampled_E':100.}
    for mode,folder in [('train','training'),('test','results')]:
        for f in sorted((P/folder).glob('*.json')):
            d=json.loads(f.read_text());e=d['energy'];w=e['work_components'];m=d['layers'][-1]['metric'];states=np.loadtxt(str(f)+'.states')
            count=2048 if mode=='train' else 128;first=0 if mode=='train' else 3000000
            check=[('component sum',sum(w.values())-e['work_total'],e['work_total']),('gain movement',w['gain_learning']-e['delta_log_gains'],max(1,e['delta_log_gains'])),('b movement',w['b_learning']-e['delta_b'],max(1,e['delta_b'])),('fast drain',w['main_fast']-.75*e['fires'],max(1,e['fires']))]
            check += [(k,w[k]-v*e['input_pulses'],max(1,e['input_pulses'])) for k,v in [('aux_mark',.2),('aux_silent',.7),('aux_error',.075)]]
            for name,error,scale in check:
                rel=abs(error)/scale;audit['max_section_relative_error']=max(audit['max_section_relative_error'],rel)
                if rel>1e-8 and abs(error)>1e-6:audit['errors'].append([f.name,name,error])
            balance=e['pump_supplied']-e['work_total']-(e['sum_terminal_E']-100*e['cells']);audit['max_pump_balance_absolute_error']=max(audit['max_pump_balance_absolute_error'],abs(balance))
            if abs(balance)>1e-7*max(1,e['work_total']):audit['errors'].append([f.name,'independently integrated pump balance',balance])
            if e['continuous_E_lower_bound']<=0 or e['min_E_at_events']<e['continuous_E_lower_bound']-1e-8:audit['errors'].append([f.name,'reserve'])
            audit['minimum_continuous_E_bound']=min(audit['minimum_continuous_E_bound'],e['continuous_E_lower_bound']);audit['minimum_sampled_E']=min(audit['minimum_sampled_E'],e['min_E_at_events'])
            found=0;complete=0
            for train in d['output_events']:
                c=collections.Counter(x[1] for x in train);found+=sum(c[first+i]==1 for i in range(count));complete+=len(train)==count and [x[1] for x in train]==list(range(first,first+count))
            if mode=='test' and (found!=m['found'] or (complete==12)!=m['full_network_word']):audit['errors'].append([f.name,'raw output recount'])
            if states.shape!=(1560,7) or not np.all(np.isfinite(states)):audit['errors'].append([f.name,'terminal states'])
            capped=float(np.mean(states[:,:3]>=math.log(4)-1e-10))
            r=dict(mode=mode,level=d['level'],seed=d['seed'],condition=d['condition'],work=e['work_total'],pump_window=e['pump_supplied'],**w,cap_fraction=capped,mean_gain=float(np.exp(states[:,:3]).mean()),mean_b=float(states[:,3].mean()),recall=found/(12*count),full_word=complete==12,tail_recall=m['recall'],tail_full_word=m['full_network_word'],relative_rms=m['relative_rms'],max_relative_error=m['max_relative_error'],continuous_E_bound=e['continuous_E_lower_bound'],sampled_E_min=e['min_E_at_events'],initial_hash=d['initial_checkpoint_sha256'])
            rows.append(r);data[mode,d['level'],d['seed'],d['condition']]=r;audit['dataset_count']+=1
    fields=[(-1,0)]+[(l,s) for l in range(3) for s in range(20)]
    for l,s in fields:
        a=data['test',l,s,'gate_on'];b=data['test',l,s,'gate_off']
        if a['initial_hash']!=b['initial_hash']:audit['errors'].append([l,s,'unmatched intervention'])
        else:audit['matched_checkpoint_pairs']+=1
        for condition in ['normal_frozen','uniform4_frozen']:
            if data['test',l,s,condition]['initial_hash']!=a['initial_hash']:audit['errors'].append([l,s,'unmatched frozen b'])
        if data['train',l,s,'gate_on']['initial_hash']!=data['train',l,s,'gate_off']['initial_hash']:audit['errors'].append([l,s,'unmatched nominal acquisition'])
    expected=122+305
    if len(rows)!=expected:audit['errors'].append(['dataset count',len(rows),expected])
    with (P/'metrics.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    grouped=collections.defaultdict(list)
    for r in rows:grouped[r['mode'],r['level'],r['condition']].append(r)
    groups=[]
    for (mode,l,c),rs in sorted(grouped.items()):
        groups.append(dict(mode=mode,level=l,condition=c,n=len(rs),full_words=sum(r['full_word'] for r in rs),tail_full_words=sum(r['tail_full_word'] for r in rs),means={k:float(np.mean([r[k] for r in rs])) for k in ['work','recall','tail_recall','cap_fraction','mean_gain','mean_b']+COMP}))
    rng=np.random.default_rng(20261025);pairs=[]
    def compare(kind,l,aa,bb):
        n=len(aa);ix=rng.integers(n,size=(20000,n));a=np.array([x['work'] for x in aa]);b=np.array([x['work'] for x in bb]);delta=a-b
        pct=100*(a.mean()/b.mean()-1);bpct=100*(a[ix].mean(axis=1)/b[ix].mean(axis=1)-1)
        out=dict(comparison=kind,level=l,n=n,direction='gate-on minus gate-off; secondary: learned frozen minus uniform4 frozen',mean_work_on=float(a.mean()),mean_work_off=float(b.mean()),relative_percent=float(pct),relative_percent_CI95=np.quantile(bpct,[.025,.975]).tolist(),mean_delta=float(delta.mean()),mean_delta_CI95=np.quantile(delta[ix].mean(axis=1),[.025,.975]).tolist(),full_words_on=sum(r['full_word'] for r in aa),full_words_off=sum(r['full_word'] for r in bb),recall_on=float(np.mean([r['recall'] for r in aa])),recall_off=float(np.mean([r['recall'] for r in bb])),cap_fraction_on=float(np.mean([r['cap_fraction'] for r in aa])),cap_fraction_off=float(np.mean([r['cap_fraction'] for r in bb])),mean_component_delta={k:float(np.mean([x[k]-y[k] for x,y in zip(aa,bb)])) for k in COMP},pair_work_deltas=delta.tolist())
        pairs.append(out)
    for l in [-1,0,1,2]:
        seeds=[0] if l==-1 else range(20)
        get=lambda mode,c:[data[mode,l,s,c] for s in seeds]
        compare('same_state_gate_intervention',l,get('test','gate_on'),get('test','gate_off'))
        compare('acquisition_from_same_nominal_state',l,get('train','gate_on'),get('train','gate_off'))
        compare('trained_policy_test',l,get('test','gate_on'),get('test','trained_off'))
        compare('secondary_frozen_gain_assignment',l,get('test','normal_frozen'),get('test','uniform4_frozen'))
        aa=[];bb=[]
        for s in seeds:
            for trainc,testc,target in [('gate_on','gate_on',aa),('gate_off','trained_off',bb)]:
                tr=data['train',l,s,trainc];te=data['test',l,s,testc]
                target.append({**te,**{k:tr[k]+te[k] for k in ['work']+COMP}})
        compare('one_acquisition_plus_one_test',l,aa,bb)
    (P/'summary.json').write_text(json.dumps(dict(groups=groups,paired_comparisons=pairs),indent=2))
    (P/'AUDIT.json').write_text(json.dumps(audit,indent=2))
    print(json.dumps(audit));
    if audit['errors']:raise RuntimeError('audit failed')
    for p in pairs:print(p['comparison'],p['level'],round(p['relative_percent'],6),p['relative_percent_CI95'],p['full_words_on'],p['full_words_off'])
if __name__=='__main__':main()
