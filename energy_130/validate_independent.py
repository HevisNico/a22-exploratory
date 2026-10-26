"""Independent state-equation oracle: no C++ energy terms or switch times are read.

Integrates q, all three m and z, b, E, nine work integrals, and pump input.
Main/auxiliary thresholds and parameter caps are located by SciPy events.
This is a local numerical cross-check, not an interval certificate.
"""
import json, math, pathlib, subprocess, hashlib
import numpy as np
from scipy.integrate import solve_ivp

P=pathlib.Path(__file__).resolve().parent
A=math.log(4); K=.5; R=.1; RM=.025
LM=math.log(1.25)/.02; LS=math.log(8)/1.06; LE=math.log(4)/.15
M=(1-RM)/(A/(A-K)*(math.exp(-K*.02)-math.exp(-A*.02)))

def reference(case):
    y=np.zeros(19);y[0]=case['q'];y[1:4]=RM;y[4:7]=np.log(case['g']);y[7]=case['b'];y[8]=100
    phase=0;aux=np.zeros(3,dtype=int);raw={};fast_end=math.inf
    capped=np.array(case['g'])>=4;bcapped=case['b']>=1.1
    external=sorted([(p['time'],0,i) for i,p in enumerate(case['pulses'])]+[(p['time']+1,1,i) for i,p in enumerate(case['pulses'])])
    idx=0;t=0.;fires=[];smallest_E=100.;steps=0
    while idx<len(external) or phase or np.any(aux):
        steps+=1
        if steps>2000:raise RuntimeError('oracle event budget')
        hard=min(external[idx][0] if idx<len(external) else math.inf, fast_end)
        if not math.isfinite(hard):hard=t+20
        def rhs(time, v):
            dy=np.zeros(19);pin=np.zeros(3)
            for port,i in raw.items():
                p=case['pulses'][i];pin[port]=p['amp']*A*math.exp(-A*(time-p['time']))
            w=np.zeros(9)
            if phase==0:dy[0]=K*(R-v[0])+np.dot(np.exp(v[4:7]),pin);w[0]=np.dot(np.exp(v[4:7]),pin)
            elif phase==1:dy[0]=-A*v[0];w[1]=A*v[0]
            else:dy[0]=-v[7]*v[0];w[2]=1.1
            dz=np.zeros(3);db=0.
            for p,h in enumerate(aux):
                if h==0:dy[1+p]=K*(RM-v[1+p])+M*pin[p];w[3]+=M*pin[p]
                else:
                    rate=[0,LM,LS,LE][h];drain=rate*v[1+p];dy[1+p]=-drain;w[3+h]+=drain
                    if not case['frozen'] and v[8]>0:
                        if h==3 and (phase==0 or case['ungated']) and not capped[p]:dz[p]=8*drain
                        if h==1 and phase!=0 and not bcapped:db+=.5*drain
            dy[4:7]=dz;dy[7]=db;w[7]=sum(dz);w[8]=db
            dy[8]=10*(100-v[8])-sum(w);dy[9:18]=w;dy[18]=10*(100-v[8]);return dy
        guards=[];names=[]
        def guard(name,index,value,direction):
            def event(time,v):return v[index]-value
            event.terminal=True;event.direction=direction;guards.append(event);names.append(name)
        if phase==0:guard(('fire',0),0,1,1)
        elif phase==2:guard(('ready',0),0,R,-1)
        for p,h in enumerate(aux):guard(('aux',p),1+p,[1,.8,.1,RM][h],1 if h==0 else -1)
        if not case['frozen']:
            for p in range(3):
                if not capped[p]:guard(('zcap',p),4+p,math.log(4),1)
            if not bcapped:guard(('bcap',0),7,1.1,1)
        if hard>t+1e-13:
            sol=solve_ivp(rhs,(t,hard),y,method='DOP853',events=guards,rtol=3e-11,atol=3e-12,max_step=.12)
            if not sol.success:raise RuntimeError(sol.message)
            y=sol.y[:,-1];t=sol.t[-1];smallest_E=min(smallest_E,float(sol.y[8].min()))
            for j,ev in enumerate(sol.t_events):
                if len(ev):
                    name,p=names[j]
                    if name=='fire':y[0]=1.;phase=1;fast_end=t+1.;fires.append(t)
                    elif name=='ready':y[0]=R;phase=0
                    elif name=='aux':y[1+p]=[1,.8,.1,RM][aux[p]];aux[p]=(aux[p]+1)%4
                    elif name=='zcap':y[4+p]=math.log(4);capped[p]=True
                    elif name=='bcap':y[7]=1.1;bcapped=True
        else:t=hard
        if abs(t-fast_end)<1e-11:phase=2;y[0]=.25;fast_end=math.inf
        while idx<len(external) and abs(external[idx][0]-t)<1e-11:
            _,kind,i=external[idx];p=case['pulses'][i]['port']
            if kind==0:raw[p]=i
            else:raw.pop(p,None)
            idx+=1
    return dict(time=t,q=y[0],z=y[4:7].tolist(),b=y[7],E=y[8],work=y[9:18].tolist(),pump=y[18],events=fires,min_sample_E=smallest_E)

def run_cpp(c):
    inp=[*np.log(c['g']),c['b'],c['q'],int(c['frozen']),int(c['ungated']),len(c['pulses'])]
    lines=[' '.join(map(str,inp))]+[f"{p['time']:.17g} {i} {p['amp']:.17g} {p['port']}" for i,p in enumerate(c['pulses'])]
    r=subprocess.run([str(P/'validation/fixture_bridge')],input='\n'.join(lines)+'\n',text=True,capture_output=True,check=True)
    return json.loads(r.stdout)

def main():
    rng=np.random.default_rng(483091);cases=[]
    specifications=[([.3,2,.3],.08,False,False),([3.8]*3,1.09,False,True),([4]*3,.08,True,False),([.3]*3,.08,True,False),([1.1,1.6,.7],.5,False,False),([1.1,1.6,.7],.5,False,True)]
    for index,(g,b,frozen,ungated) in enumerate(specifications):
        for pattern in range(4):
            pulses=[]
            for k in range(3):
                for port in range(3):
                    if pattern==3 and port==2:continue
                    pulses.append(dict(time=float(.2+k*[20,4,2.5,7][pattern]+port*.037+rng.uniform(0,.01)),port=port,amp=float(rng.uniform(.75,1.25))))
            cases.append(dict(name=f'law_{index}_pattern_{pattern}',g=g,b=b,q=.1,frozen=frozen,ungated=ungated,pulses=pulses))
    cases.append(dict(name='no_input',g=[.3,1.2,.3],b=.08,q=.1,frozen=False,ungated=False,pulses=[]))
    results=[]
    for c in cases:
        a=run_cpp(c);b=reference(c)
        if len(a['events'])!=len(b['events']):raise AssertionError((c['name'],'fire count',a,b))
        errors={'event_time':max([abs(x-y) for x,y in zip(a['events'],b['events'])] or [0]),'work':float(np.max(np.abs(np.array(a['work'])-b['work']))),'reserve':abs(a['E']-b['E']),'pump':abs(a['pump']-b['pump']),'state':max(abs(a['state']['q']-b['q']),abs(a['state']['b']-b['b']),max(abs(x-y) for x,y in zip(a['state']['z'],b['z']))),'terminal_time':abs(a['state']['time']-b['time'])}
        if max(errors.values())>2e-6:raise AssertionError((c['name'],errors,a,b))
        if b['min_sample_E']<=0:raise AssertionError('depletion outside campaign scope')
        results.append(dict(name=c['name'],errors=errors,cpp=a,independent=b))
        print(c['name'],errors,flush=True)
    (P/'validation/cases.json').write_text(json.dumps(cases,indent=2))
    (P/'validation/independent_results.json').write_text(json.dumps(results,indent=2))
    summary={'status':'PASS','cases':len(results),'max_errors':{k:max(r['errors'][k] for r in results) for k in results[0]['errors']},'independence':'Raw input and initial state only shared. State ODE, event guards, work rates and pump ODE independently implemented in Python. No exported C++ work terms or switch times used.','scope':'Local nominal-parameter cases, not a global hybrid proof; no E=0 cases.'}
    summary['production_binary_sha256']=hashlib.sha256((P/'experiment').read_bytes()).hexdigest()
    summary['tested_cpp_sources_sha256']={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((P/'src').glob('*'))}
    (P/'VALIDATION.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
