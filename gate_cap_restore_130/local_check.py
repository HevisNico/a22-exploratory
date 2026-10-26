import ctypes as c,math,json,pathlib
P=pathlib.Path(__file__).resolve().parent
class Pulse(c.Structure):_fields_=[('t',c.c_double),('label',c.c_longlong),('amp',c.c_double),('port',c.c_int)]
class Output(c.Structure):_fields_=[('t',c.c_double),('label',c.c_longlong)]
class State(c.Structure):_fields_=[('z',c.c_double*3),('b',c.c_double),('q',c.c_double),('time',c.c_double),('phase',c.c_int)]
fn=c.CDLL(str(P/'validation/instrumented.so')).point_cell
fn.argtypes=[c.POINTER(Pulse),c.c_int,c.POINTER(State),c.c_int,c.c_int,c.c_double,c.POINTER(Output),c.c_int,c.POINTER(State),c.POINTER(State),c.POINTER(c.c_longlong),c.POINTER(c.c_double),c.c_longlong,c.c_char_p,c.c_int];fn.restype=c.c_int
results=[]
for ungated in [0,1]:
 initial=State((c.c_double*3)(*map(math.log,[.3,2.,.3])),.08,.1,0,0);terminal=State();before=State();moves=c.c_longlong();diag=(c.c_double*8)();error=c.create_string_buffer(512);out=(Output*20)();pulse=Pulse(.1,1,1.,1)
 n=fn(c.byref(pulse),1,c.byref(initial),0,ungated,0,out,20,c.byref(terminal),c.byref(before),c.byref(moves),diag,0,error,512)
 assert n>=0,error.value
 inc=terminal.z[1]-initial.z[1]
 assert abs(diag[6]+diag[7]-.6)<1e-12
 assert abs(inc-(.6 if ungated else 0))<1e-12,(inc,ungated)
 results.append({'ungated':bool(ungated),'log_gain_increment':inc,'demand_ready':diag[6],'demand_protected':diag[7],'events':n})
(P/'LOCAL_ANALYTIC_CHECK.json').write_text(json.dumps(results,indent=2));print(results)
