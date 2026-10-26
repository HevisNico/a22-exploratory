"""Native acceleration of the point simulator only; not the certified A22 engine."""
from kernel import *
import ctypes as ct
class Pulse(ct.Structure):_fields_=[('time',ct.c_double),('label',ct.c_longlong),('amp',ct.c_double),('port',ct.c_int)]
class Output(ct.Structure):_fields_=[('time',ct.c_double),('label',ct.c_longlong)]
class State(ct.Structure):_fields_=[('z',ct.c_double*3),('b',ct.c_double),('q',ct.c_double),('time',ct.c_double),('phase',ct.c_int)]
lib=ct.CDLL(str(Path(__file__).with_name('point_cell.so')))
fn=lib.point_cell
fn.argtypes=[ct.POINTER(Pulse),ct.c_int,ct.POINTER(State),ct.c_int,ct.c_double,ct.POINTER(Output),ct.c_int,ct.POINTER(State),ct.POINTER(State),ct.POINTER(ct.c_longlong),ct.c_char_p,ct.c_int]
fn.restype=ct.c_int
def cell(trains,params,initial,charge_kicks=None,rule='normal',freeze_at=float('inf'),probe_start=4096.):
    assert len(trains)==3 and not charge_kicks and rule=='normal' and freeze_at in (0.,math.inf)
    assert all(all(abs(x-y)<1e-12 for x,y in zip(p,[4,LM0,LS0,LE0,M0])) for p in params)
    data=[]
    for p,train in enumerate(trains):
        for t,label,amp,decay,width in train:
            assert decay==A and width==1.
            data.append(Pulse(t,-1 if label is None else label,amp,p))
    incoming=(Pulse*len(data))(*data);capacity=2*len(data)+16;out=(Output*capacity)()
    st=State((ct.c_double*3)(*initial['z']),initial['b'],initial['q'],0.,0)
    terminal=State();before=State();moves=ct.c_longlong();error=ct.create_string_buffer(512)
    n=fn(incoming,len(data),ct.byref(st),int(freeze_at==0),probe_start,out,capacity,ct.byref(terminal),ct.byref(before),ct.byref(moves),error,len(error))
    if n<0:raise ArithmeticError(error.value.decode())
    def snapshot(x):return {'z':list(x.z),'g':[math.exp(v) for v in x.z],'b':x.b,'q':x.q,'time':x.time,'phase':x.phase}
    return [(out[i].time,None if out[i].label<0 else out[i].label) for i in range(n)],{'after_probes':snapshot(terminal),'after_training':snapshot(before),'probe_gain_moves':moves.value}
