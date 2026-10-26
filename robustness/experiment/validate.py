import json,math
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
import extended_simulate as s
root=Path(__file__).parent
data=json.loads((root/'output/baseline.json').read_text())
ref=json.loads((root.parent/'A22_point_simulator_kit/sources/historical_nominal_events.json').read_text());by={}
for n,j,t in ref:by.setdefault((int(n),int(j)),[]).append(t)
errs=[];bad=[]
for c in data['cells']:
    aa=[t for t,l in c['training_events']];bb=by.get((c['layer'],c['lane']),[])
    if len(aa)!=len(bb):bad.append([c['layer'],c['lane'],len(aa),len(bb)])
    else:errs.extend(abs(a-b) for a,b in zip(aa,bb))
assert not bad and max(errs)<1e-8
tests=[]
for decay in [s.A*.9,s.A,s.A*1.1]:
    for width in [.9,1.,1.05]:
        amp=.75/(-math.expm1(-decay*width))
        for k in [3,5,7]:
            gains=[.6/(k-1)]*k;gains[k//2]=1.2
            params=[[4,s.LM0,s.LS0,s.LE0,s.M0] for _ in range(k)]
            events,_=s.cell([[(0.,0,amp,decay,width)]]*k,params,{'z':list(map(math.log,gains)),'q':.1,'b':.08})
            def f(t,y):return [s.K*(s.R-y[0])+sum(gains)*amp*decay*math.exp(-decay*t),s.K*(s.RM-y[1])+s.M0*amp*decay*math.exp(-decay*t)]
            def threshold(t,y):return y[0]-1
            threshold.terminal=True;threshold.direction=1
            sol=solve_ivp(f,[0,width],[s.R,s.RM],rtol=2e-12,atol=1e-13,events=threshold,max_step=.005)
            err=abs(events[0][0]-sol.t_events[0][0]);assert err<1e-8
            tests.append({'decay':decay,'width':width,'parents':k,'first_spike_error_vs_solve_ivp':err})
out={'nominal':{'events':len(errs),'mismatches':bad,'max_date_error':max(errs)},'independent_ODE_checks':tests,'max_ODE_error':max(x['first_spike_error_vs_solve_ivp'] for x in tests),'status':'PASS'}
(root/'VALIDATION.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='independent_ODE_checks'}))
