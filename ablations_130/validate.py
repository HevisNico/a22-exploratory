import json,math,random,time
from pathlib import Path
import kernel as new
import reference_kernel as old
P=Path(__file__).parent
params=[[4,new.LM0,new.LS0,new.LE0,new.M0] for _ in range(3)]
initial={'z':list(map(math.log,[.3,1.2,.3])),'q':.1,'b':.08}
source=[(8.*i,i,1.,new.A,1.) for i in range(128)]
parents=[source]+[[] for _ in range(11)]
reference=json.loads((P.parent/'A22_point_simulator_kit/sources/historical_nominal_events.json').read_text());ref={}
for n,j,t in reference:ref.setdefault((int(n),int(j)),[]).append(t)
diff=[];count=0
for n in range(1,19):
    row=[]
    for j in range(12):
        out,info=new.cell([parents[(j-1)%12],parents[j],parents[(j+1)%12]],params,initial)
        aa=[t for t,l in out];bb=ref.get((n,j),[])
        assert len(aa)==len(bb),(n,j,len(aa),len(bb))
        diff.extend(abs(a-b) for a,b in zip(aa,bb));count+=len(aa)
        row.append([(t,l,1.,new.A,1.) for t,l in out])
    parents=row
assert max(diff)<1e-8
# Exact local checks of the intended gates and of the recovery ablation.
trains=[[(0.,128,1.,new.A,1.)]]*3
checks={}
for rule in ['normal','none','ungated']:
    out,info=new.cell(trains,params,{'z':[math.log(3)]*3,'q':.1,'b':.08},rule=rule)
    checks[rule]=info['after_probes']
assert all(abs(g-3)<1e-12 for g in checks['normal']['g'])
assert all(abs(g-4)<1e-12 for g in checks['ungated']['g'])
assert checks['none']['b']==.08
late=[[(t,128,1.,new.A,1.)] for t in [0.,.3,.3]]
_,late_info=new.cell(late,params,{'z':[math.log(3)]*3,'q':.1,'b':.08})
assert late_info['after_probes']['b']>.08
# No perturbation: the new normal rule agrees with the previous kernel.
rng=random.Random(45)
trains=[[(8.*i+(.003*rng.random()),i,math.exp(.1*rng.gauss(0,1)-.005),new.A,1.) for i in range(12)] for p in range(3)]
a,ia=new.cell(trains,params,initial);b,ib=old.cell(trains,params,initial)
assert len(a)==len(b)
localerr=max(abs(x[0]-y[0]) for x,y in zip(a,b))
assert localerr<1e-8
assert max(abs(x-y) for x,y in zip(ia['after_probes']['g'],ib['after_probes']['g']))<1e-8
_,u=new.cell([[(0.,128,1.,new.A,1.)]]*3,params,{'z':[math.log(1.5)]*3,'q':.1,'b':.08},rule='ungated')
_,f=new.cell([[(0.,128,1.,new.A,1.)]]*3,params,{'z':[math.log(1.5)]*3,'q':.1,'b':.08},rule='ungated',freeze_at=0.)
assert max(abs(g-1.5*math.exp(.6)) for g in u['after_probes']['g'])<1e-10
assert f['after_probes']['g']==[1.5]*3 and f['after_probes']['b']==.08
result={'status':'PASS','historical_events':count,'max_historical_date_error':max(diff),'local_noisy_old_vs_new_error':localerr,'gate_checks':checks,'uncapped_ungated_gain_expected':1.5*math.exp(.6),'uncapped_ungated_gain_observed':u['after_probes']['g'],'frozen_from_zero_gain_observed':f['after_probes']['g'],'root':'scipy.brentq xtol=5e-14 rtol=1e-14; floating point only'}
(P/'VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='gate_checks'}))
