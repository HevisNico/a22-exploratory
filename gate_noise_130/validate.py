"""Validate new ablation and compiled network against the Python event solver."""
import ctypes as ct, json, math, sys, time
from pathlib import Path
import kernel as py
import native_kernel as native
P=Path(__file__).resolve().parent
lib=ct.CDLL(str(P/'network.so'))
noise=lib.noise_pair
noise.argtypes=[ct.c_int]*5+[ct.c_longlong,ct.c_int,ct.POINTER(ct.c_double)]
def pair(seed,n,j,p,stage,label,occ):
    out=(ct.c_double*2)();noise(seed,n,j,p,stage,label,occ,out);return tuple(out)
def inputs(row,seed,n,j,stage,sigma,jitter):
    from collections import Counter
    result=[]
    for p in range(3):
        seen=Counter();train=[]
        for ordinal,(t,label) in enumerate(row[(j+p-1)%12]):
            occ=seen[label];seen[label]+=1
            z,u=pair(seed,n,j,p,stage,label if label is not None else -1-ordinal,occ)
            train.append((t+.1+jitter*u,label,math.exp(sigma*z-sigma*sigma/2),py.A,1.))
        result.append(train)
    return result
def local():
    errors=[];maxdate=maxgain=maxb=0.
    for level in range(3):
        row=[[(8.*i,i) for i in range(48)] for _ in range(12)]
        trains=inputs(row,7,9,3,0,.05*(level+1),.015*(level+1))
        for rule in ['normal','ungated']:
            for frozen in [False,True]:
                initial={'z':list(map(math.log,[.3,1.2,.3])),'q':.1,'b':.08}
                a,ai=py.cell(trains,[[4,py.LM0,py.LS0,py.LE0,py.M0]]*3,initial,rule=rule,freeze_at=0. if frozen else math.inf,probe_start=0.)
                b,bi=native.cell(trains,[[4,py.LM0,py.LS0,py.LE0,py.M0]]*3,initial,rule=rule,freeze_at=0. if frozen else math.inf,probe_start=0.)
                if [l for t,l in a]!=[l for t,l in b]:errors.append([level,rule,frozen])
                maxdate=max(maxdate,max((abs(t-u) for (t,l),(u,k) in zip(a,b)),default=0))
                maxgain=max(maxgain,max(abs(x-y) for x,y in zip(ai['after_probes']['z'],bi['after_probes']['z'])))
                maxb=max(maxb,abs(ai['after_probes']['b']-bi['after_probes']['b']))
    assert not errors and maxdate<1e-7 and maxgain<1e-7 and maxb<1e-7
    return {'cases':12,'label_mismatches':errors,'max_time_error':maxdate,'max_log_gain_error':maxgain,'max_b_error':maxb}
def full(N=512,rule='normal',seed=0,level=1):
    ref=json.loads((P/f'validation/pilot_{rule}.json' if rule!='normal' else P/'validation/pilot.json').read_text())
    row=[[(8.*i,i) for i in range(N)]]+[[] for _ in range(11)];errors=[];metric_errors=[];maxz=maxb=maxt=0.
    pars=[[4,py.LM0,py.LS0,py.LE0,py.M0]]*3
    for n in range(1,131):
        nextrow=[]
        for j in range(12):
            tr=inputs(row,seed,n,j,0,.05*(level+1),.015*(level+1))
            init={'z':list(map(math.log,[.3,1.2,.3])),'q':.1,'b':.08}
            out,info=py.cell(tr,pars,init,rule=rule,probe_start=math.inf)
            st=info['after_probes'];oracle=ref['training'][n-1]['cells'][j]['state']
            maxz=max(maxz,max(abs(x-y) for x,y in zip(st['z'],oracle['z'])));maxb=max(maxb,abs(st['b']-oracle['b']));maxt=max(maxt,abs(st['time']-oracle['time']))
            nextrow.append(out)
        row=nextrow
        import native_run
        tailrow=[[(t,l) for t,l in tr if (l is not None and N-128<=l<N) or (l is None and t>=8*(N-128))] for tr in row]
        met=native_run.pulse_metrics(tailrow,[8.*i for i in range(N-128,N)],N-128)
        expected=ref['training'][n-1]['tail128']
        for key in ['found','expected','complete_lanes','events','ambiguous','duplicates','outside_labels']:
            if met[key]!=expected[key]:metric_errors.append([n,key,met[key],expected[key]])
        if maxz>1e-5 or maxb>1e-5 or maxt>1e-5:errors.append(n)
    assert not errors and not metric_errors,(errors,metric_errors,maxz,maxb,maxt)
    return {'N':N,'rule':rule,'seed':seed,'max_log_gain_error':maxz,'max_b_error':maxb,'max_terminal_time_error':maxt,'bad_layers':errors,'metric_errors':metric_errors}
if __name__=='__main__':
    result={'local':local()};print(json.dumps(result),flush=True)
    if '--full' in sys.argv:result['network_python_oracle']=full()
    result['status']='PASS';(P/'VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
