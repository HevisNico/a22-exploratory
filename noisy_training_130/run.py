"""Long noisy training followed by independent tests, with held-out randomness.
Decisions to extend training use training data only; all twenty seeds retained.
"""
import argparse,collections,concurrent.futures,hashlib,json,math,random,time,traceback
from pathlib import Path
import kernel as s
P=Path(__file__).parent;OUT=P/'output';TEST_LABEL=1000000
PAR=[[4,s.LM0,s.LS0,s.LE0,s.M0] for _ in range(3)]
SELECTED={18,68,80,100,130}
def noise(seed,n,j,p,label,ordinal,occ):
    ident=f'{seed}:{n}:{j}:{p}:{label}:{occ if label is not None else ordinal}'.encode()
    rng=random.Random(int.from_bytes(hashlib.blake2b(ident,digest_size=16).digest(),'big'))
    return rng.gauss(0,1),rng.uniform(-math.sqrt(3),math.sqrt(3))
def dates(count):
    out=[0.]
    for i in range(count-1):out.append(out[-1]+20*[1,1.1,1.05,1.2,1,1.15][i%6])
    return out
def pulse_metrics(cells,source_dates,start_label):
    N=len(source_dates);found=complete=events=ambiguous=duplicates=extra=0;rel=[]
    for c in cells:
        by=collections.defaultdict(list)
        for t,label in c:
            events+=1
            if label is None:ambiguous+=1
            else:by[label].append(t)
        found+=sum(len(by[start_label+i])==1 for i in range(N))
        complete+=len(c)==N and all(len(by[start_label+i])==1 for i in range(N))
        duplicates+=sum(max(0,len(v)-1) for v in by.values())
        extra+=sum(len(v) for k,v in by.items() if k<start_label or k>=start_label+N)
        for i in range(N-1):
            if len(by[start_label+i])==len(by[start_label+i+1])==1:
                gap=source_dates[i+1]-source_dates[i]
                rel.append(((by[start_label+i+1][0]-by[start_label+i][0])-gap)/gap)
    return {'found':found,'expected':12*N,'recall':found/(12*N),'complete_lanes':complete,'full_network_word':complete==12,'events':events,'ambiguous':ambiguous,'duplicates':duplicates,'outside_labels':extra,'interval_pairs':len(rel),'relative_rms':math.sqrt(sum(e*e for e in rel)/len(rel)) if rel else None,'max_relative_error':max(map(abs,rel),default=None)}
def trains_for(parents,seed,n,j,stage,sigma,jitter,N,train_counts=None):
    trains=[]
    for p,parent in enumerate([(j-1)%12,j,(j+1)%12]):
        train=[];counts=collections.Counter()
        for ordinal,(t,label) in enumerate(parents[parent]):
            occ=counts[label];counts[label]+=1
            key=label;idx=ordinal
            if stage=='training' and label is not None and label>=128:key=f'extra_training:{label}'
            elif stage=='primary':
                key=128+label-TEST_LABEL if label is not None else None
                idx+=train_counts.get((n-1,parent),0)
            elif stage=='long':key=f'heldout_long:{label}:{ordinal if label is None else occ}'
            if sigma or jitter:z,u=noise(seed,n,j,p,key,idx,occ)
            else:z=u=0.
            amp=math.exp(sigma*z-sigma*sigma/2);arrival=t+.1+jitter*u
            assert arrival>=t
            train.append((arrival,label,amp,s.A,1.))
        train.sort();trains.append(train)
    return trains
def train(seed,N,sigma=.1,jitter=.03):
    parents=[[(8.*i,i) for i in range(N)]]+[[] for _ in range(11)]
    records=[];profiles=[];states={};counts={(0,0):N};tail64=[]
    for n in range(1,131):
        row=[];tailrow=[]
        for j in range(12):
            trains=trains_for(parents,seed,n,j,'training',sigma,jitter,N)
            initial={'z':list(map(math.log,[.3,1.2,.3])),'q':.1,'b':.08}
            events,info=s.cell(trains,PAR,initial,probe_start=math.inf)
            state=info['after_probes'];assert state['phase']==0
            states[n,j]=state;counts[n,j]=len(events);row.append(events)
            tail=[(t,l) for t,l in events if (l is not None and N-64<=l<N) or (l is None and t>=8.*(N-64))]
            tailrow.append(tail)
            records.append({'layer':n,'lane':j,'training_count':len(events),'end_state':state,'tail64_events':tail,'events_sha256':hashlib.sha256(json.dumps(events,separators=(',',':')).encode()).hexdigest()})
        metric=pulse_metrics(tailrow,[8.*i for i in range(N-64,N)],N-64)
        profiles.append({'layer':n,'training_events':sum(len(e) for e in row),'tail64':metric})
        parents=row
    # No decision uses test outcomes. This is an operational criterion, not a theorem.
    prepared=profiles[-1]['tail64']['full_network_word']
    return {'N':N,'prepared_observed':prepared,'cells':records,'layers':profiles},states,counts
def test(seed,N,states,counts,stage='primary',count=24,freeze=False,sigma=.1,jitter=.03):
    source=dates(count);parents=[[(t,TEST_LABEL+i) for i,t in enumerate(source)]]+[[] for _ in range(11)]
    # Keep the same 3080-unit source silence as in the old 128-pulse protocol.
    test_start=4096.+8*(N-128);profiles=[];records=[];min_quiet=math.inf
    for n in range(1,131):
        row=[]
        for j in range(12):
            before=states[n,j];quiet=test_start-before['time'];assert quiet>0
            min_quiet=min(min_quiet,quiet)
            initial={'z':before['z'][:],'b':before['b'],'q':s.R+(before['q']-s.R)*math.exp(-s.K*quiet)}
            trains=trains_for(parents,seed,n,j,stage,sigma,jitter,N,counts)
            events,info=s.cell(trains,PAR,initial,probe_start=0.,freeze_at=0. if freeze else math.inf)
            row.append(events)
            rec={'layer':n,'lane':j,'before':initial,'after':info['after_probes'],'gain_moves':info['probe_gain_moves']}
            if n in SELECTED:rec['events']=events
            records.append(rec)
        profiles.append({'layer':n,**pulse_metrics(row,source,TEST_LABEL)});parents=row
    return {'stage':stage,'pulses':count,'freeze':freeze,'source_dates_relative':source,'time_origin':test_start,'minimum_quiet_time':min_quiet,'layers':profiles,'cells':records}
def run(seed,quiet=False,fixed_N=None):
    name=f'quiet_{fixed_N or 512}' if quiet else f'seed_{seed}'
    dest=OUT/(name+'.json')
    if dest.exists():return {'name':name,'cached':True}
    start=time.monotonic();sigma=0. if quiet else .1;jitter=0. if quiet else .03
    attempts=[]
    try:
        for N in ([fixed_N] if fixed_N else [512,1024,2048]):
            training,states,counts=train(seed,N,sigma,jitter)
            attempts.append({'N':N,'prepared_observed':training['prepared_observed'],'layer130_tail64':training['layers'][-1]['tail64']})
            # Preserve a reproducible checkpoint, including unsuccessful attempts.
            checkpoint=OUT/f'{name}_training_{N}.json';tmp=checkpoint.with_suffix('.tmp');tmp.write_text(json.dumps(training,separators=(',',':')));tmp.replace(checkpoint)
            if training['prepared_observed'] or fixed_N:break
        tests=[]
        for stage,count in [('primary',24),('long',128)]:
            for freeze in [False,True]:tests.append(test(seed,N,states,counts,stage,count,freeze,sigma,jitter))
        result={'status':'OK_POINT_NOT_CERTIFIED','name':name,'seed':seed,'quiet':quiet,'sigma':sigma,'jitter':jitter,'training_attempts':attempts,'training_N':N,'prepared_observed':training['prepared_observed'],'tests':tests,'seconds':time.monotonic()-start}
    except Exception as e:result={'status':'UNSUPPORTED_OR_ERROR','name':name,'seed':seed,'error':repr(e),'traceback':traceback.format_exc(),'seconds':time.monotonic()-start}
    tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(result,separators=(',',':')));tmp.replace(dest)
    return {'name':name,'status':result['status'],'seconds':round(result['seconds'],2),'training_N':result.get('training_N'),'prepared':result.get('prepared_observed'),'error':result.get('error')}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);ap.add_argument('--pilot',action='store_true');ap.add_argument('--start-seed',type=int,default=0);a=ap.parse_args();OUT.mkdir(exist_ok=True)
    jobs=[(0,False,None)] if a.pilot else [(seed,False,None) for seed in range(a.start_seed,20)]+[(0,True,512)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as ex:
        futures=[ex.submit(run,*args) for args in jobs]
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):print(json.dumps({'done':i,'total':len(jobs),**f.result()}),flush=True)
