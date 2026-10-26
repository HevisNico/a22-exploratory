"""Exploratory point arithmetic for nominal physical parameters, not a validator.

Fresh cells start at time zero with the authorized nominal q, m, b and a
specified authorized perturbation of initial logarithmic gains. All incoming
emissions are retained; no terminal gain is substituted for training history.
Auxiliary offsets are exact nominal solutions of the physical auxiliary ODEs.
No original A22 module, native extension or campaign runner is imported.
"""
import argparse, bisect, hashlib, json, math, time
from pathlib import Path

A=math.log(4); K=.5; R=.1; LM=math.log(1.25)/.02; LE=A/.15
LOGCAP=math.log(4); LOG25=math.log(2.5)
ROOT=Path(__file__).resolve().parent
PROBES=[4096.+20*k for k in range(4)]

def root(f,hi):
    # Point bisection: reproducible, but NOT outward-rounded validation.
    lo=0.
    assert f(lo)<=1e-11 and f(hi)>=-1e-11,(f(lo),f(hi),hi)
    for _ in range(48):
        m=(lo+hi)*.5
        if f(m)>=0:hi=m
        else:lo=m
    return (lo+hi)*.5

def cell(trains,eta):
    external=[]
    for p,train in enumerate(trains):
        assert all(y-x>1.8329 for x,y in zip(train,train[1:]))
        for s in train:
            for age,kind in [(0.,0),(.02,1),(.04,2),(1.,3),(1.10,4),(1.25,5)]:
                external.append((s+age,kind,p,s))
    external.sort()
    z=[math.log(g)+eta for g in (.3,1.2,.3)]
    q=R;b=.08;t=0.;phase=0;fast_end=math.inf
    raw=[None]*3;marks=[None]*3;errors=[None]*3;out=[];idx=0
    training_state=None;gate_events=0;closest_internal_external=math.inf
    def snapshot():return {'g':[math.exp(x) for x in z],'z':z[:],'b':b,'q':q,'phase':phase,'time':t}
    while idx<len(external) or phase!=0:
        ext=external[idx][0] if idx<len(external) else math.inf
        if training_state is None and ext>=PROBES[0] and phase==0:
            assert not any(x is not None for x in raw+marks+errors)
            training_state=snapshot()
        target=ext
        if phase==1:target=min(target,fast_end)
        if not math.isfinite(target):
            assert phase==2
            target=t+20
        dt=target-t
        assert dt>=-1e-10,(t,target)
        dt=max(0.,dt)
        mc=sum(math.exp(-LM*(t-s)) for s in marks if s is not None)
        B=.5*mc if b<1.1 else 0.
        captime=math.inf
        if B>0 and 0<(1.1-b)<B:
            captime=-math.log1p(-(1.1-b)/B)/LM
        def intb(u):
            v=min(u,captime)
            return b*v+B*(v+math.expm1(-LM*v)/LM)+1.1*max(0.,u-v)
        internal=None
        if phase==0 and dt>0:
            J=sum(math.exp(z[p])*A*math.exp(-A*(t-s)) for p,s in enumerate(raw) if s is not None)
            C=q-R+J/(A-K);D=J/(A-K)
            peak=math.log(A*D/(K*C))/(A-K) if C>0 and D>0 else 0.
            upto=min(dt,max(0.,peak))
            def charge(u):return R+C*math.exp(-K*u)-D*math.exp(-A*u)
            if upto>0 and charge(upto)>=1:
                dt=root(lambda u:charge(u)-1,upto);internal='fire'
        elif phase==2 and intb(dt)>=math.log(q/R):
            needed=math.log(q/R)
            dt=root(lambda u:intb(u)-needed,dt);internal='ready'
        oldphase=phase
        if phase==0:
            J=sum(math.exp(z[p])*A*math.exp(-A*(t-s)) for p,s in enumerate(raw) if s is not None)
            q=R+(q-R)*math.exp(-K*dt)+J*(math.exp(-K*dt)-math.exp(-A*dt))/(A-K)
            for p,s in enumerate(errors):
                if s is not None:
                    assert raw[p] is None
                    inc=.8*math.exp(-LE*(t-s))*(-math.expm1(-LE*dt))
                    if inc>0 and z[p]<LOGCAP:gate_events+=1
                    z[p]=min(LOGCAP,z[p]+inc)
        elif phase==1:q*=math.exp(-A*dt)
        else:q*=math.exp(-intb(dt))
        if oldphase!=0:b=min(1.1,b+B*(-math.expm1(-LM*dt)))
        t+=dt
        if internal:
            if math.isfinite(ext):closest_internal_external=min(closest_internal_external,abs(ext-t))
            if internal=='fire':q=1.;phase=1;fast_end=t+1.;out.append(t)
            else:q=R;phase=0
            continue
        if oldphase==1 and abs(t-fast_end)<1e-9:
            q=.25;phase=2;fast_end=math.inf
        # Equal-time external changes are processed together. Nominal marks
        # at a section are continuous; point tie handling is not a proof of
        # all admissible weak-order executions.
        while idx<len(external) and abs(external[idx][0]-t)<1e-9:
            _,kind,p,s=external[idx]
            if kind==0:
                assert raw[p] is None
                raw[p]=s
            elif kind==1:marks[p]=s+.02
            elif kind==2:marks[p]=None
            elif kind==3:raw[p]=None
            elif kind==4:errors[p]=s+1.10
            else:errors[p]=None
            idx+=1
    if training_state is None:training_state=snapshot()
    return out,{'after_training':training_state,'after_probes':snapshot(),
       'ready_error_subintervals':gate_events,
       'closest_internal_external_point_gap':closest_internal_external if math.isfinite(closest_internal_external) else None}

def run_case(name,depth):
    source=[8.*k for k in range(128)]+PROBES
    parents=[source]+[[] for _ in range(11)];records=[];start=time.time()
    for n in range(1,depth+1):
        row=[]
        for j in range(12):
            eta={'nominal':0.,'plus':1e-5,'minus':-1e-5,
                 'interface':1e-5 if j<6 else -1e-5,
                 'plus_prefix18':1e-5 if n<=18 else 0.,
                 'minus_prefix18':-1e-5 if n<=18 else 0.}[name]
            trains=[parents[(j-1)%12],parents[j],parents[(j+1)%12]]
            events,info=cell(trains,eta);row.append(events)
            train=[x for x in events if x<PROBES[0]]
            probe=[x for x in events if x>=PROBES[0]]
            lat=[x-s for x,s in zip(probe,PROBES)] if len(probe)==4 else None
            records.append({'layer':n,'lane':j,'initial_log_gain_shift':eta,
                'training_events':train,'probe_events':probe,'probe_latencies':lat,**info})
        parents=row
        if n%8==0 or n==depth:print(json.dumps({'case':name,'layer':n,'elapsed_seconds':round(time.time()-start,2),'training_outputs':sum(len(r['training_events']) for r in records[-12:])}),flush=True)
    result={'status':'EXPLORATORY POINT DIAGNOSTIC; NOT AN INTERVAL CERTIFICATE',
       'case':name,'depth':depth,'source_training':[8*k for k in range(128)],
       'source_probes':PROBES,'physical_parameters':'nominal; authorized initial z shifts only',
       'new_cell_state':'Fresh authorized initial state at time zero; full incoming train retained',
       'cells':records,'elapsed_seconds':time.time()-start,
       'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    path=ROOT/'results'/('point_'+name+'.json');path.write_text(json.dumps(result,indent=2)+'\n')
    return result

def compare_historical(result):
    ref=json.loads((ROOT/'inputs'/'historical_nominal_events.json').read_text())
    by={}
    for n,j,t in ref:by.setdefault((int(n),int(j)),[]).append(t)
    count_mismatches=[];maxerr=0.;total=0
    for r in result['cells']:
        if r['layer']>18:continue
        expected=by.get((r['layer'],r['lane']),[]);actual=r['training_events'];total+=len(actual)
        if len(expected)!=len(actual):count_mismatches.append([r['layer'],r['lane'],len(expected),len(actual)])
        else:maxerr=max(maxerr,max((abs(x-y) for x,y in zip(actual,expected)),default=0.))
    out={'historical_events':len(ref),'diagnostic_events_first_18':total,
         'count_mismatches':count_mismatches,'maximum_point_date_difference':maxerr,
         'status':'PASS regression only' if not count_mismatches and maxerr<1e-5 else 'FAIL diagnostic not accepted'}
    (ROOT/'results'/'historical_regression.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out),flush=True)
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case',choices=['nominal','plus','minus','interface','plus_prefix18','minus_prefix18'],default='nominal');ap.add_argument('--depth',type=int,default=18);args=ap.parse_args()
    assert 1<=args.depth<=192
    res=run_case(args.case,args.depth)
    if args.case=='nominal' and args.depth>=18:
        regression=compare_historical(res)
        if regression['status'].startswith('FAIL'):raise SystemExit(2)
