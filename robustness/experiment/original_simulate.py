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
def root(f,hi):
    lo=0.
    if not(f(lo)<=1e-10 and f(hi)>=-1e-10):raise ArithmeticError(('root',f(lo),f(hi),hi))
    for _ in range(48):
        m=(lo+hi)*.5
        if f(m)>=0:hi=m
        else:lo=m
    return (lo+hi)*.5

def cell(trains,params,initial):
    caps,LM,LS,LE,M=([p[k] for p in params] for k in range(5))
    logcaps=list(map(math.log,caps))
    d=[root(lambda u,p=p:RM+M[p]*h(u)-1,.1) for p in range(3)]
    dm=[math.log(1.25)/x for x in LM];ds=[math.log(8)/x for x in LS];de=[A/x for x in LE]
    if min(d[p]+dm[p]+ds[p] for p in range(3))<=1:raise ArithmeticError('ERROR overlaps own raw pulse: unsupported analytic segment')
    external=[]
    for p,train in enumerate(trains):
        if any(y[0]-x[0]<1.8329 for x,y in zip(train,train[1:])):raise ArithmeticError('parent gap')
        cycle=d[p]+dm[p]+ds[p]+de[p]
        if any(y[0]-x[0]<=cycle for x,y in zip(train,train[1:])):raise ArithmeticError('auxiliary not regenerated')
        for s,label in train:
            for age,kind in [(0.,0),(d[p],1),(d[p]+dm[p],2),(1.,3),(d[p]+dm[p]+ds[p],4),(cycle,5)]:external.append((s+age,kind,p,s,label))
    external.sort();z=initial['z'][:];q=initial['q'];b=initial['b'];t=0.;phase=0;fast_end=math.inf
    raw=[None]*3;labels=[None]*3;marks=[None]*3;errors=[None]*3;out=[];idx=0
    trainstate=None;cap_hits=[];b_hit=None;gate_events=0;mix=[];near=math.inf;probe_gain_moves=0
    def snapshot():return {'z':z[:],'g':[math.exp(x) for x in z],'b':b,'q':q,'phase':phase,'time':t}
    while idx<len(external) or phase!=0:
        ext=external[idx][0] if idx<len(external) else math.inf
        if trainstate is None and ext>=PROBES[0] and phase==0:
            if any(x is not None for x in raw+marks+errors):raise ArithmeticError('uncleared training state')
            trainstate=snapshot()
        target=min(ext,fast_end) if phase==1 else ext
        if not math.isfinite(target):
            if phase!=2:raise ArithmeticError('unexpected infinite target')
            target=t+20
        dt=max(0.,target-t)
        Bs=[.5*math.exp(-LM[p]*(t-s)) if s is not None else 0. for p,s in enumerate(marks)]
        if b>=1.1:Bs=[0.]*3
        def db(u):return sum(Bs[p]*(-math.expm1(-LM[p]*u)) for p in range(3))
        captime=root(lambda u:db(u)-(1.1-b),dt) if b<1.1 and b+db(dt)>1.1 else math.inf
        def intb(u):
            v=min(u,captime)
            return b*v+sum(Bs[p]*(v+math.expm1(-LM[p]*v)/LM[p]) for p in range(3))+1.1*max(0.,u-v)
        internal=None
        if phase==0 and dt>0:
            J=sum(math.exp(z[p])*A*math.exp(-A*(t-s)) for p,s in enumerate(raw) if s is not None)
            C=q-R+J/(A-K);D=J/(A-K)
            peak=math.log(A*D/(K*C))/(A-K) if C>0 and D>0 else 0.;upto=min(dt,max(0.,peak))
            def charge(u):return R+C*math.exp(-K*u)-D*math.exp(-A*u)
            if upto>0 and charge(upto)>=1:dt=root(lambda u:charge(u)-1,upto);internal='fire'
        elif phase==2 and intb(dt)>=math.log(q/R):
            needed=math.log(q/R);dt=root(lambda u:intb(u)-needed,dt);internal='ready'
        oldphase=phase
        if phase==0:
            J=sum(math.exp(z[p])*A*math.exp(-A*(t-s)) for p,s in enumerate(raw) if s is not None)
            q=R+(q-R)*math.exp(-K*dt)+J*(math.exp(-K*dt)-math.exp(-A*dt))/(A-K)
            for p,s in enumerate(errors):
                if s is None:continue
                if raw[p] is not None:raise ArithmeticError('own raw/error overlap')
                amp=.8*math.exp(-LE[p]*(t-s));inc=amp*(-math.expm1(-LE[p]*dt))
                if inc>0 and z[p]<logcaps[p]:
                    gate_events+=1
                    if t>=PROBES[0]:probe_gain_moves+=1
                    if z[p]+inc>=logcaps[p]:
                        contact=t-math.log1p(-(logcaps[p]-z[p])/amp)/LE[p]
                        cap_hits.append({'port':p,'time':contact})
                z[p]=min(logcaps[p],z[p]+inc)
        elif phase==1:q*=math.exp(-A*dt)
        else:q*=math.exp(-intb(dt))
        if oldphase!=0:
            if captime<=dt and b_hit is None:b_hit=t+captime
            b=min(1.1,b+db(dt))
        t+=dt
        if internal:
            if math.isfinite(ext):near=min(near,abs(ext-t))
            if internal=='fire':
                live=[labels[p] for p in range(3) if raw[p] is not None]
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
            elif kind==1:marks[p]=s+d[p]
            elif kind==2:marks[p]=None
            elif kind==3:raw[p]=None;labels[p]=None
            elif kind==4:errors[p]=s+d[p]+dm[p]+ds[p]
            else:errors[p]=None
            idx+=1
    if trainstate is None:trainstate=snapshot()
    return out,{'after_training':trainstate,'after_probes':snapshot(),'gain_cap_hits':cap_hits,'b_cap_hit':b_hit,'ready_error_subintervals':gate_events,'probe_gain_moves':probe_gain_moves,'mixed_label_firings':mix,'closest_event_gap':near if math.isfinite(near) else None}

def parameters(case,n,j,rng,eta_override=None):
    eps=case['eps'];style=case['style'];values=[]
    for p in range(3):
        if style=='uniform':ss=[rng.uniform(-1,1) for _ in range(5)]
        elif style=='corners':ss=[rng.choice([-1,1]) for _ in range(5)]
        elif style=='checker':ss=[(-1)**(n+j+p+k) for k in range(5)]
        elif style=='split':ss=[(1 if j<6 else -1)*(-1)**k for k in range(5)]
        else:ss=case.get('signs',[0]*5)
        values.append([x*(1+eps*s) for x,s in zip([4,LM0,LS0,LE0,M0],ss)])
    radius=case.get('initial_alpha',1e-5)
    shifts=[rng.uniform(-radius,radius) for _ in range(3)] if case.get('vary_initial') else [0.]*3
    if eta_override is not None:shifts=[eta_override]*3
    elif 'fixed_gain_shift' in case:shifts=[case['fixed_gain_shift']]*3
    initial={'z':[math.log(g)+v for g,v in zip([.3,1.2,.3],shifts)],'q':R+(rng.uniform(-1e-5,1e-5) if case.get('vary_initial') else 0),'b':.08+(rng.uniform(-1e-5,1e-5) if case.get('vary_initial') else 0),'auxiliary':'READY exactly rm'}
    return values,initial

def widths(cells):
    by={};mixed=0;duplicates=[]
    for j,c in enumerate(cells):
        for t,k in c['training_events']:
            if k is None:mixed+=1;continue
            if j in by.setdefault(k,{}):duplicates.append((k,j))
            by[k][j]=t
    complete={k:p for k,p in by.items() if len(p)==12 and not any(z[0]==k for z in duplicates)}
    cohorts=[];ordered=sorted(complete)
    for pos,k in enumerate(ordered):
        p=complete[k];D=max(p.values())-min(p.values());W=max(max(p[i%12] for i in [j-1,j,j+1])-min(p[i%12] for i in [j-1,j,j+1]) for j in range(12))
        # A dense pair is identified by actual same-lane next-cohort gaps <15.5,
        # not by assigning the kth emission to an assumed pulse index.
        gaps=[complete[ordered[pos+1]][j]-p[j] for j in range(12)] if pos+1<len(ordered) else []
        cohorts.append({'source_label':k,'D':D,'local_triplet_spread':W,'gap_to_next_min':min(gaps) if gaps else None,'gap_to_next_max':max(gaps) if gaps else None,'dense_pair_start':bool(gaps and min(gaps)<15.5)})
    dense=[c for c in cohorts if c['dense_pair_start']]
    return {'complete_cohorts':len(cohorts),'partial_labels':len(by)-len(complete),'mixed_label_firings':mixed,'duplicate_labels':duplicates,'max_D':max((c['D'] for c in cohorts),default=None),'max_local_spread':max((c['local_triplet_spread'] for c in cohorts),default=None),'dense_pair_count':len(dense),'max_dense_D':max((c['D'] for c in dense),default=None),'max_dense_local_spread':max((c['local_triplet_spread'] for c in dense),default=None),'cohorts':cohorts}

def run(case):
    start=time.monotonic();rng=random.Random(case['seed']);source=[(8.*k,k) for k in range(128)]+[(s,128+i) for i,s in enumerate(PROBES)]
    parents=[source]+[[] for _ in range(11)];records=[];layers=[]
    for n in range(1,case['depth']+1):
        row=[];cells=[]
        for j in range(12):
            pars,initial=parameters(case,n,j,rng);events,info=cell([parents[(j-1)%12],parents[j],parents[(j+1)%12]],pars,initial)
            row.append(events);c={'layer':n,'lane':j,'parameters':pars,'initial':initial,'training_events':[x for x in events if x[0]<4096],'probe_events':[x for x in events if x[0]>=4096],**info};records.append(c);cells.append(c)
        layers.append({'layer':n,**widths(cells)});parents=row
    result={'status':'EXPLORATORY_POINT_SIMULATION_NOT_CERTIFIED','case':case,'cells':records,'layers':layers,'seconds':time.monotonic()-start}
    (ROOT/'results').mkdir(exist_ok=True);(ROOT/'results'/f"{case['name']}.json").write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(case['name'],round(result['seconds'],2),'D18',layers[17]['max_D'],'denseD18',layers[17]['max_dense_D'],'mixed',sum(x['mixed_label_firings'] for x in layers),flush=True)
    return {'case':case,'seconds':result['seconds'],'layers':layers}

def regression():
    c={'name':'nominal','eps':0.,'style':'fixed','seed':0,'depth':24};r=run(c)
    data=json.loads((ROOT/'results/nominal.json').read_text());ref=json.loads((ROOT/'sources/historical_nominal_events.json').read_text());by={}
    for n,j,t in ref:by.setdefault((int(n),int(j)),[]).append(t)
    errors=[];mismatches=[]
    for cellrow in data['cells']:
        if cellrow['layer']>18:continue
        aa=[t for t,k in cellrow['training_events']];bb=by.get((cellrow['layer'],cellrow['lane']),[])
        if len(aa)!=len(bb):mismatches.append([cellrow['layer'],cellrow['lane'],len(aa),len(bb)])
        else:errors.extend(abs(a-b) for a,b in zip(aa,bb))
    v={'mismatches':mismatches,'max_date_error':max(errors),'events_compared':len(errors),'status':'PASS_NOMINAL_REGRESSION' if not mismatches and max(errors)<1e-5 else 'FAIL'}
    (ROOT/'REGRESSION.json').write_text(json.dumps(v,indent=2)+'\n')
    if v['status']=='FAIL':raise ArithmeticError(v)
    return r

def main():
    start=time.monotonic();rows=[regression()];cases=[]
    for i,signs in enumerate([[1]*5,[-1]*5,[1,-1,1,-1,1],[-1,1,-1,1,-1]]):cases.append({'name':f'coherent_{i}','eps':.01,'style':'fixed','signs':signs,'seed':i,'depth':24})
    for style in ['checker','split']:cases.append({'name':style,'eps':.01,'style':style,'seed':42,'depth':24})
    for style in ['uniform','corners']:
        for seed in range(8):cases.append({'name':f'{style}_{seed}','eps':.01,'style':style,'seed':seed+1024,'depth':24,'vary_initial':True})
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as ex:
        for r in ex.map(run,cases):rows.append(r)
    (ROOT/'CAMPAIGN.json').write_text(json.dumps({'status':'EXPLORATORY_NOT_CERTIFIED','cases':rows,'wall_seconds':time.monotonic()-start},indent=2)+'\n')
if __name__=='__main__':main()
