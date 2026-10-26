"""Point event-driven diagnostics, never an interval certificate.
Per-port fixed parameters; full training and four separated probes retained.
The nominal analytic simulator is included in sources/ for regression.
"""
import json,math,random,time,hashlib,itertools,concurrent.futures
from pathlib import Path
A=math.log(4);K=.5;R=.1;RM=.025;LOG25=math.log(2.5)
LM0=math.log(1.25)/.02;LS0=math.log(8)/1.06;LE0=A/.15
def h(t):return A/(A-K)*(math.exp(-K*t)-math.exp(-A*t))
M0=.975/h(.02);PROBES=[4096.+20*k for k in range(4)]
ROOT=Path(__file__).resolve().parent
from scipy.optimize import brentq
def root(f,hi):
    flo=f(0.);fhi=f(hi)
    if flo>1e-10 or fhi < -1e-10:raise ArithmeticError(('root',flo,fhi,hi))
    if flo>=0:return 0.
    if fhi<=0:return hi
    return brentq(f,0.,hi,xtol=5e-14,rtol=1e-14)

def cell(trains,params,initial,charge_kicks=None,rule="normal",freeze_at=float("inf"),probe_start=4096.):
    assert rule in ("normal","none","ungated","gain_frozen")
    N=len(trains)
    charge_kicks=charge_kicks or {}
    caps,LM,LS,LE,M=([p[k] for p in params] for k in range(5))
    logcaps=list(map(math.log,caps))
    dm=[math.log(1.25)/x for x in LM];ds=[math.log(8)/x for x in LS];de=[A/x for x in LE]
    external=[];pulses={};delays={};delay_cache={}
    for p,train in enumerate(trains):
        previous_end=-math.inf
        for s,label,amplitude,decay,width in train:
            assert amplitude>0 and decay>K and width>0
            def response(u):
                return amplitude*decay/(decay-K)*(math.exp(-K*u)-math.exp(-decay*u))
            peak=min(width,math.log(decay/K)/(decay-K))
            if RM+M[p]*response(peak)<1:
                raise ArithmeticError('auxiliary subthreshold: residual memory needs full auxiliary solver')
            cache_key=(p,amplitude,decay,width)
            if cache_key not in delay_cache:delay_cache[cache_key]=root(lambda u:RM+M[p]*response(u)-1,peak)
            d=delay_cache[cache_key]
            cycle=d+dm[p]+ds[p]+de[p]
            if s<=previous_end:raise ArithmeticError('auxiliary not regenerated')
            if d+dm[p]+ds[p]<=width:raise ArithmeticError('ERROR overlaps own raw pulse')
            previous_end=s+max(cycle,width)
            pulses[p,s]=(amplitude,decay,width);delays[p,s]=d
            for age,kind in [(0.,0),(d,1),(d+dm[p],2),(width,3),(d+dm[p]+ds[p],4),(cycle,5)]:
                external.append((s+age,kind,p,s,label))
    external.sort();z=initial['z'][:];q=initial['q'];b=initial['b'];t=0.;phase=0;fast_end=math.inf
    raw=[None]*N;labels=[None]*N;marks=[None]*N;errors=[None]*N;out=[];idx=0
    trainstate=None;cap_hits=[];b_hit=None;gate_events=0;mix=[];near=math.inf;probe_gain_moves=0
    def snapshot():return {'z':z[:],'g':[math.exp(x) for x in z],'b':b,'q':q,'phase':phase,'time':t}
    while idx<len(external) or phase!=0:
        ext=external[idx][0] if idx<len(external) else math.inf
        if trainstate is None and ext>=probe_start and phase==0:
            if any(x is not None for x in raw+marks+errors):raise ArithmeticError('uncleared training state')
            trainstate=snapshot()
        target=min(ext,fast_end) if phase==1 else ext
        if not math.isfinite(target):
            if phase!=2:raise ArithmeticError('unexpected infinite target')
            target=t+20
        dt=max(0.,target-t)
        Bs=[.5*math.exp(-LM[p]*(t-s)) if s is not None else 0. for p,s in enumerate(marks)]
        if b>=1.1 or rule=="none" or t>=freeze_at:Bs=[0.]*N
        activeB=[(B,LM[p]) for p,B in enumerate(Bs) if B]
        def db(u):return sum(B*(-math.expm1(-rate*u)) for B,rate in activeB)
        captime=root(lambda u:db(u)-(1.1-b),dt) if b<1.1 and b+db(dt)>1.1 else math.inf
        def intb(u):
            v=min(u,captime)
            return b*v+sum(B*(v+math.expm1(-rate*v)/rate) for B,rate in activeB)+1.1*max(0.,u-v)
        internal=None
        terms=[(math.exp(z[p])*pulses[p,s][0]*pulses[p,s][1]*math.exp(-pulses[p,s][1]*(t-s)),pulses[p,s][1]) for p,s in enumerate(raw) if s is not None]
        def charge(u):
            ek=math.exp(-K*u)
            return R+(q-R)*ek+sum(J*(ek-math.exp(-decay*u))/(decay-K) for J,decay in terms)
        if phase==0 and dt>0:
            if all(decay==A for J,decay in terms):
                J=sum(J for J,decay in terms)
                C=q-R+J/(A-K);D=J/(A-K)
                peak=math.log(A*D/(K*C))/(A-K) if C>0 and D>0 else 0.
                upto=min(dt,max(0.,peak))
                def charge(u):return R+C*math.exp(-K*u)-D*math.exp(-A*u)
            else:
                # derivative times exp(K*u) is strictly decreasing for positive inputs.
                def derivative_scaled(u):
                    return -K*(q-R)+sum(J*(-K+decay*math.exp(-(decay-K)*u))/(decay-K) for J,decay in terms)
                if derivative_scaled(0)<=0:upto=0.
                elif derivative_scaled(dt)>=0:upto=dt
                else:upto=root(lambda u:-derivative_scaled(u),dt)
            if upto>0 and charge(upto)>=1:dt=root(lambda u:charge(u)-1,upto);internal='fire'
        elif phase==2 and intb(dt)>=math.log(q/R):
            needed=math.log(q/R);dt=root(lambda u:intb(u)-needed,dt);internal='ready'
        oldphase=phase
        if phase==0:
            q=charge(dt)
        elif phase==1:q*=math.exp(-A*dt)
        else:q*=math.exp(-intb(dt))
        if rule not in ("none","gain_frozen") and t<freeze_at and (oldphase==0 or rule=="ungated"):
            for p,s in enumerate(errors):
                if s is None:continue
                if raw[p] is not None:raise ArithmeticError('own raw/error overlap')
                amp=.8*math.exp(-LE[p]*(t-s));inc=amp*(-math.expm1(-LE[p]*dt))
                if inc>0 and z[p]<logcaps[p]:
                    gate_events+=1
                    if t>=probe_start:probe_gain_moves+=1
                    if z[p]+inc>=logcaps[p]:
                        contact=t-math.log1p(-(logcaps[p]-z[p])/amp)/LE[p]
                        cap_hits.append({'port':p,'time':contact})
                z[p]=min(logcaps[p],z[p]+inc)
        if oldphase!=0:
            if captime<=dt and b_hit is None:b_hit=t+captime
            b=min(1.1,b+db(dt))
        t+=dt
        if internal:
            if math.isfinite(ext):near=min(near,abs(ext-t))
            if internal=='fire':
                live=[labels[p] for p in range(N) if raw[p] is not None]
                unique=set(live)
                label=next(iter(unique)) if len(unique)==1 and None not in unique else None
                if label is None:mix.append({'time':t,'parent_labels':live})
                q=1.;phase=1;fast_end=t+1.;out.append((t,label))
            else:q=R;phase=0
            continue
        if oldphase==1 and abs(t-fast_end)<1e-9:q=.25;phase=2;fast_end=math.inf
        while idx<len(external) and abs(external[idx][0]-t)<1e-9:
            _,kind,p,s,label=external[idx]
            if kind==0:
                if raw[p] is not None:raise ArithmeticError('overlapping raw pulses')
                raw[p]=s;labels[p]=label
                if phase==0:q=max(0.,q+charge_kicks.get((p,label),0.))
            elif kind==1:marks[p]=s+delays[p,s]
            elif kind==2:marks[p]=None
            elif kind==3:raw[p]=None;labels[p]=None
            elif kind==4:errors[p]=s+delays[p,s]+dm[p]+ds[p]
            else:errors[p]=None
            idx+=1
        if phase==0 and q>=1:
            live=[labels[p] for p in range(N) if raw[p] is not None]
            unique=set(live)
            label=next(iter(unique)) if len(unique)==1 and None not in unique else None
            if label is None:mix.append({'time':t,'parent_labels':live})
            q=1.;phase=1;fast_end=t+1.;out.append((t,label))
    if trainstate is None:trainstate=snapshot()
    return out,{'after_training':trainstate,'after_probes':snapshot(),'gain_cap_hits':cap_hits,'b_cap_hit':b_hit,'ready_error_subintervals':gate_events,'probe_gain_moves':probe_gain_moves,'mixed_label_firings':mix,'closest_event_gap':near if math.isfinite(near) else None}
