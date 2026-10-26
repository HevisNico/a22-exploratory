import numpy as np,math,subprocess,json,sys
from scipy.integrate import solve_ivp
from pilot import P,NOM,write,read,sha,evaljob,prepare

def oracle(params,g,b,pulses,frozen):
 A=math.log(4);y=np.array([.1,.025,.025,.025,*np.log(g),b],dtype=float);phase=0;aux=[0]*3;raw={};fast=math.inf;t=0;idx=0;fires=[]
 ext=sorted([(p[0],0,i) for i,p in enumerate(pulses)]+[(p[0]+1,1,i) for i,p in enumerate(pulses)])
 capped=[g[p]>=params[p][0] for p in range(3)];bcapped=b>=1.1
 for step in range(3000):
  # Snap already-reached projected boundaries before restarting solve_ivp.
  # Without this, a cap reached within rounding at an external boundary can
  # be missed by the next event search and spuriously overshoot.
  if y[7]>=1.1-5e-12:y[7]=1.1;bcapped=True
  for p in range(3):
   if y[4+p]>=math.log(params[p][0])-5e-12:y[4+p]=math.log(params[p][0]);capped[p]=True
  if idx==len(ext) and phase==0 and aux==[0]*3:return dict(events=fires,z=y[4:7].tolist(),b=float(y[7]))
  hard=min(ext[idx][0] if idx<len(ext) else math.inf,fast)
  if not math.isfinite(hard):hard=t+20
  def rhs(time,v):
   dy=np.zeros(8);pin=np.zeros(3)
   for port,i in raw.items():p=pulses[i];pin[port]=p[1]*A*math.exp(-A*(time-p[0]))
   dy[0]=.5*(.1-v[0])+np.dot(np.exp(v[4:7]),pin) if phase==0 else (-A*v[0] if phase==1 else -v[7]*v[0])
   for p,h in enumerate(aux):
    c,lm,ls,le,m=params[p]
    if h==0:dy[1+p]=.5*(.025-v[1+p])+m*pin[p]
    else:
     drain=[0,lm,ls,le][h]*v[1+p];dy[1+p]=-drain
     if not frozen:
      if h==3 and phase==0 and not capped[p]:dy[4+p]=8*drain
      if h==1 and phase!=0 and not bcapped:dy[7]+=.5*drain
   return dy
  guards=[];names=[]
  def guard(name,index,value,direction):
   def e(time,v):return v[index]-value
   e.terminal=True;e.direction=direction;guards.append(e);names.append(name)
  if phase==0:guard(('fire',0),0,1,1)
  if phase==2:guard(('ready',0),0,.1,-1)
  for p,h in enumerate(aux):guard(('aux',p),1+p,[1,.8,.1,.025][h],1 if h==0 else -1)
  if not frozen:
   for p in range(3):
    if not capped[p]:guard(('cap',p),4+p,math.log(params[p][0]),1)
   if not bcapped:guard(('bcap',0),7,1.1,1)
  if hard>t+1e-13:
   sol=solve_ivp(rhs,(t,hard),y,method='DOP853',rtol=1e-11,atol=1e-12,max_step=.08,events=guards)
   assert sol.success;y=sol.y[:,-1];t=sol.t[-1]
   for i,ev in enumerate(sol.t_events):
    if len(ev):
     name,p=names[i]
     if name=='fire':y[0]=1;phase=1;fast=t+1;fires.append(t)
     elif name=='ready':y[0]=.1;phase=0
     elif name=='aux':y[1+p]=[1,.8,.1,.025][aux[p]];aux[p]=(aux[p]+1)%4
     elif name=='cap':y[4+p]=math.log(params[p][0]);capped[p]=True
     elif name=='bcap':y[7]=1.1;bcapped=True
  else:t=hard
  if abs(t-fast)<1e-11:y[0]=.25;phase=2;fast=math.inf
  while idx<len(ext) and abs(ext[idx][0]-t)<1e-11:
   _,kind,i=ext[idx];port=pulses[i][2]
   if kind==0:raw[port]=i
   else:raw.pop(port,None)
   idx+=1
 raise RuntimeError('oracle budget')

def main():
 prepare();rng=np.random.default_rng(20261026);cases=[]
 for j in range(12):
  # Also exercise wider perturbations locally to detect rate/index mistakes.
  eps=[0,1e-4,.02][j%3];params=[[float(v*(1+rng.uniform(-eps,eps))) for v in NOM] for p in range(3)]
  g=[.3,1.2,.3] if j<6 else [3.8,3.8,3.8];b=.08 if j%2==0 else .9;frozen=j>=9
  pulses=[[float(.2+k*[4,2.5,8][j%3]+p*.051+rng.uniform(0,.008)),float(rng.uniform(.8,1.2)),p] for k in range(4) for p in range(3)]
  lines=[' '.join(map(str,p)) for p in params]+[' '.join(map(str,[*np.log(g),b,.1,int(frozen),len(pulses)]))]+[' '.join(map(str,p)) for p in pulses]
  r=subprocess.run([str(P/'bin/bridge')],input='\n'.join(lines)+'\n',capture_output=True,text=True,check=True);a=json.loads(r.stdout);o=oracle(params,g,b,pulses,frozen)
  assert len(a['events'])==len(o['events']),(j,a,o)
  err=max([abs(x-y) for x,y in zip(a['events'],o['events'])]+[abs(a['state']['b']-o['b'])]+[abs(x-y) for x,y in zip(a['state']['z'],o['z'])])
  assert err<2e-7,(j,err,a,o)
  cases.append(dict(index=j,epsilon=eps,params=params,g=g,b=b,frozen=frozen,pulses=pulses,max_event_or_state_error=err,cpp=a,ode=o));print('ODE check',j,'passed',err,flush=True)
 old=P.parent/'restored/A22_targeted_noise_selectivity_diagnostic_EN'
 for seed in [1000,1002]:
  st=old/'states'/f's{seed}_learned.states';dest=P/'checks'/f'nominal_s{seed}_regression.json'
  # Field selector uses nominal field for either seed; original sigma/jitter preserved.
  new=evaljob(seed,'nominal_noisy',st,'baseline',dest);prior=read(old/'results'/f's{seed}_learned_noise_only.json')
  assert new['output_events']==prior['output_events'] and new['layer_event_counts']==prior['layer_event_counts']
  assert new['energy']['work_components']==prior['energy']['work_components']
  print('Nominal full-network regression',seed,'exact',flush=True)
 write(P/'checks/ODE_CASES.json',cases)
 write(P/'checks/VALIDATION.json',dict(status='PASS',independent_ode_cases=12,max_error=max(c['max_event_or_state_error'] for c in cases),nominal_full_network_regressions=[1000,1002],scope='Local independent ODE state/event checks and two exact nominal network replays; not global interval certification.'))
if __name__=='__main__':main()
