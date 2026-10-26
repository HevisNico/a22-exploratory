"""Independent Python propagation of the primary fully-fixed baseline."""
import ctypes as ct,json,math
from collections import Counter
from pathlib import Path
import kernel as py
P=Path(__file__).resolve().parent
def run():
    source=json.loads((P/'output/fixed_all_L0_S0_gap20.json').read_text());ref=next(t for t in source['tests'] if t['pulses']==24)
    lib=ct.CDLL(str(P/'network.so'));fn=lib.noise_pair;fn.argtypes=[ct.c_int]*5+[ct.c_longlong,ct.c_int,ct.POINTER(ct.c_double)];v=(ct.c_double*2)()
    dates=[0.];gaps=[1,1.1,1.05,1.2,1,1.15]
    for i in range(23):dates.append(dates[-1]+20*gaps[i%6])
    row=[[(t,1000000+i) for i,t in enumerate(dates)]]+[[] for _ in range(11)];problems=[]
    for layer in range(1,131):
        nextrow=[]
        for lane in range(12):
            trains=[]
            for port in range(3):
                tr=[];counts=Counter()
                for ordinal,(t,label) in enumerate(row[(lane+port-1)%12]):
                    occ=counts[label];counts[label]+=1;fn(0,layer,lane,port,24,label if label is not None else -1-ordinal,occ,v)
                    tr.append((t+.1+.015*v[1],label,math.exp(.05*v[0]-.05*.05/2),py.A,1.))
                trains.append(tr)
            events,_=py.cell(trains,[[4,py.LM0,py.LS0,py.LE0,py.M0]]*3,{'z':[math.log(4)]*3,'b':.08,'q':.1},freeze_at=0.,probe_start=0.);nextrow.append(events)
        found=complete=events=ambiguous=duplicates=0
        for tr in nextrow:
            labels=[l for _,l in tr];counts=Counter(labels);found+=sum(counts[1000000+i]==1 for i in range(24));complete+=labels==list(range(1000000,1000024));events+=len(tr);ambiguous+=counts[None];duplicates+=sum(max(0,n-1) for k,n in counts.items() if k is not None)
        expected=ref['layers'][layer-1]['metric']
        for k,value in [('found',found),('complete_lanes',complete),('events',events),('ambiguous',ambiguous),('duplicates',duplicates)]:
            if expected[k]!=value:problems.append([layer,k,value,expected[k]])
        row=nextrow
    maxdate=0.
    for a,b in zip(row,ref['output_events']):
        if [l if l is not None else -1 for _,l in a]!=[l for _,l in b]:problems.append(['final labels'])
        maxdate=max(maxdate,max((abs(t-u) for (t,l),(u,k) in zip(a,b)),default=0))
    assert not problems and maxdate<1e-7,(problems,maxdate)
    result={'status':'PASS','scope':'Fully-fixed gains4 b0.08, primary24 impulses, low noise seed0, all130 layers against Python solver','max_final_output_time_difference':maxdate,'discrete_mismatches':problems};(P/'validation/PYTHON_NETWORK.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':print(json.dumps(run(),indent=2))
