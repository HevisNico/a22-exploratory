import json,math,random,time
from pathlib import Path
import native_kernel as n,kernel as p,native_run
P=Path(__file__).parent
def local():
    rng=random.Random(771);dates=[];gains=[];mismatch=[]
    pars=[[4,n.LM0,n.LS0,n.LE0,n.M0]]*3
    for case in range(12):
        trains=[[(8.*i+rng.uniform(0,.05),i,math.exp(.1*rng.gauss(0,1)-.005),n.A,1.) for i in range(64)] for _ in range(3)]
        initial={'z':list(map(math.log,[.3,1.2,.3] if case<6 else [.99,3.1,.8])),'q':.1,'b':.08 if case<6 else .6}
        frozen=case%2==1
        a,ai=p.cell(trains,pars,initial,freeze_at=0. if frozen else math.inf,probe_start=0.)
        b,bi=n.cell(trains,pars,initial,freeze_at=0. if frozen else math.inf,probe_start=0.)
        if [l for t,l in a]!=[l for t,l in b]:mismatch.append(case)
        dates.extend(abs(x[0]-y[0]) for x,y in zip(a,b));gains.extend(abs(x-y) for x,y in zip(ai['after_probes']['g'],bi['after_probes']['g']))
    assert not mismatch and max(dates)<1e-8 and max(gains)<1e-8
    return {'cases':12,'label_mismatches':mismatch,'max_date_error':max(dates),'max_gain_error':max(gains)}
if __name__=='__main__':
    result={'local':local()};print('local PASS',flush=True)
    native_run.OUT.mkdir(exist_ok=True)
    print(native_run.run(0),flush=True)
    native=json.loads((P/'output_native/seed_0.json').read_text())
    pilot=P/'pilot_not_counted/seed_0.json'
    if not pilot.exists():pilot=P/'output/seed_0.json'
    oracle=json.loads(pilot.read_text())
    oldtrain=pilot.with_name('seed_0_training_512.json')
    ref=json.loads(oldtrain.read_text());new=json.loads((P/'output_native/seed_0_training_512.json').read_text())
    mismatch=[];gain=[];date=[]
    for a,b in zip(ref['cells'],new['cells']):
        if a['training_count']!=b['training_count'] or [l for t,l in a['tail64_events']]!=[l for t,l in b['tail64_events']]:mismatch.append(['training',a['layer'],a['lane']])
        gain.extend(abs(x-y) for x,y in zip(a['end_state']['g'],b['end_state']['g']))
        date.extend(abs(x[0]-y[0]) for x,y in zip(a['tail64_events'],b['tail64_events']))
    for a,b in zip(oracle['tests'],native['tests']):
        for x,y in zip(a['layers'],b['layers']):
            if any(x[k]!=y[k] for k in ['events','found','complete_lanes','ambiguous','duplicates']):mismatch.append(['test',a['stage'],a['freeze'],x['layer']])
        for x,y in zip(a['cells'],b['cells']):
            gain.extend(abs(v-w) for v,w in zip(x['after']['g'],y['after']['g']))
            if 'events' in x:
                if [l for t,l in x['events']]!=[l for t,l in y['events']]:mismatch.append(['test_labels',a['stage'],a['freeze'],x['layer'],x['lane']])
                date.extend(abs(v[0]-w[0]) for v,w in zip(x['events'],y['events']))
    result['full_512_training_and_four_tests']={'mismatches':mismatch,'max_gain_error':max(gain),'max_date_error':max(date)}
    result['status']='PASS' if not mismatch and max(gain)<1e-6 and max(date)<1e-6 else 'FAIL'
    (P/'NATIVE_VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);assert result['status']=='PASS'
