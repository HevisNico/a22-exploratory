"""Validate full-fixed and gain-only-fixed modes against the Python solver."""
import ctypes as ct,json,math
from pathlib import Path
import kernel as py,native_kernel as native
P=Path(__file__).resolve().parent
def run():
    lib=ct.CDLL(str(P/'network.so'));fn=lib.noise_pair
    fn.argtypes=[ct.c_int]*5+[ct.c_longlong,ct.c_int,ct.POINTER(ct.c_double)]
    pars=[[4,py.LM0,py.LS0,py.LE0,py.M0]]*3;out=(ct.c_double*2)();errors=[];maxdate=maxz=maxb=0.;cases=0
    for level in range(3):
        for gap in [8.,20.]:
            trains=[]
            for port in range(3):
                tr=[]
                for label in range(32):
                    fn(7,3,6,port,0,label,0,out);z,u=out;sig=.05*(level+1);jit=.015*(level+1)
                    tr.append((label*gap+.1+jit*u,label,math.exp(sig*z-sig*sig/2),py.A,1.))
                trains.append(tr)
            for mode,b0 in [(1,.08),(2,.08),(1,1.1)]:
                init={'z':[math.log(4)]*3,'b':b0,'q':.1}
                a,ai=py.cell(trains,pars,init,rule='normal' if mode==1 else 'gain_frozen',freeze_at=0. if mode==1 else math.inf,probe_start=0.)
                b,bi=native.cell(trains,pars,init,mode=mode,probe_start=0.)
                if [l for _,l in a]!=[l for _,l in b]:errors.append([level,gap,mode,'labels'])
                maxdate=max(maxdate,max((abs(x[0]-y[0]) for x,y in zip(a,b)),default=0));maxz=max(maxz,max(abs(x-y) for x,y in zip(ai['after_probes']['z'],bi['after_probes']['z'])));maxb=max(maxb,abs(ai['after_probes']['b']-bi['after_probes']['b']));cases+=1
    assert not errors and maxdate<1e-7 and maxz==0 and maxb<1e-7,(errors,maxdate,maxz,maxb)
    result={'status':'PASS','cases':cases,'label_mismatches':errors,'max_time_difference':maxdate,'max_log_gain_difference':maxz,'max_b_difference':maxb};(P/'VALIDATION.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':print(json.dumps(run(),indent=2))
