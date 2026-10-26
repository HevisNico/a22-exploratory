import pathlib,sys,json,hashlib,math,random,subprocess,concurrent.futures,time
P=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P));from scoring import audit_physics,match_times
SEEDS=list(range(3000,3006));ARMS=['nominal_quiet','nominal_noisy','uncertain_quiet','uncertain_noisy']
A=math.log(4);NOM=[4,math.log(1.25)/.02,math.log(8)/1.06,A/.15,.975/(A/(A-.5)*(math.exp(-.5*.02)-math.exp(-A*.02)))]
def read(f):return json.loads(pathlib.Path(f).read_text())
def sha(f):return hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
def write(f,d):pathlib.Path(f).write_text(json.dumps(d,indent=2))
def field(s,arm):return P/'fields'/('nominal.txt' if arm.startswith('nominal') else f's{s}.txt')
def level(arm):return 0 if arm.endswith('noisy') else -1
def prepare():
 (P/'fields').mkdir(exist_ok=True)
 manifest=[]
 for seed in [None,*SEEDS]:
  rng=random.Random(202610260000+(seed or 0));rows=[]
  for i in range(1560*3):rows.append([v if seed is None else v*(1+1e-4*rng.uniform(-1,1)) for v in NOM])
  for r in rows:
   assert all(abs(v/n-1)<=1.000001e-4 for v,n in zip(r,NOM))
  f=P/'fields'/('nominal.txt' if seed is None else f's{seed}.txt')
  f.write_text(''.join(' '.join(format(v,'.17g') for v in r)+'\n' for r in rows))
  manifest.append(dict(seed=seed,path=f.name,sha256=sha(f),relative_min=[min(r[k]/NOM[k]-1 for r in rows) for k in range(5)],relative_max=[max(r[k]/NOM[k]-1 for r in rows) for k in range(5)]))
 write(P/'FIELDS.json',manifest)
 write(P/'SOURCE_LOCK.json',dict(protocol=sha(P/'PROTOCOL.json'),sources={f.name:sha(f) for f in (P/'src').iterdir()},binaries={n:sha(P/'bin'/n) for n in ['train','evaluate','bridge']}))
 print('Prepared seven physical fields and source lock',flush=True)
def evaljob(seed,arm,st,mode,dest):
 cmd=[str(P/'bin/evaluate'),str(seed),str(level(arm)),str(st),'lateral_100' if mode=='mixed' else 'noise','mixed' if mode=='mixed' else 'clean','-1',str(dest),str(field(seed,arm))]
 r=subprocess.run(cmd,capture_output=True,text=True)
 if r.returncode:
  dest.with_suffix('.stderr.txt').write_text(r.stderr);raise RuntimeError(('evaluation',seed,arm,mode,r.returncode,r.stderr))
 d=read(dest);d['energy'].update(reserve_mode='positive_bound_work_exact',min_E_at_events=None,pump_supplied=None,sum_terminal_E=None)
 audit_physics(d)
 d['_provenance']=dict(seed=seed,arm=arm,mode=mode,field_sha256=sha(field(seed,arm)),state_sha256=sha(st),binary_sha256=sha(P/'bin/evaluate'))
 write(dest,d);return d

def job_impl(seed,arm):
 start=time.monotonic();dest=P/'results'/f's{seed}_{arm}_train.json';f=field(seed,arm)
 if dest.exists():raise RuntimeError('No unverified overwrite of pilot results')
 r=subprocess.run([str(P/'bin/train'),str(seed),str(level(arm)),str(f),str(dest)],capture_output=True,text=True)
 if r.returncode:
  dest.with_suffix('.stderr.txt').write_text(r.stderr);raise RuntimeError(('acquisition',seed,arm,r.returncode,r.stderr))
 d=read(dest);e=d['energy'];w=e['work_components']
 for k,mass in [('aux_mark',.2),('aux_silent',.7),('aux_error',.075)]:assert abs(w[k]-mass*e['input_pulses'])<1e-5+1e-8*e['input_pulses'],(seed,arm,k)
 assert e['continuous_E_lower_bound']>0 and abs(w['main_fast']-.75*e['fires'])<1e-6+1e-8*e['fires']
 st=pathlib.Path(str(dest)+'.states')
 d['_provenance']=dict(seed=seed,arm=arm,field_sha256=sha(f),state_sha256=sha(st),binary_sha256=sha(P/'bin/train'))
 write(dest,d)
 for mode in ['baseline','mixed']:
  x=evaljob(seed,arm,st,mode,P/'results'/f's{seed}_{arm}_{mode}.json')
  assert x['_provenance']['field_sha256']==d['_provenance']['field_sha256']
 return dict(seed=seed,arm=arm,training_word=d['final_training_metric']['full_network_word'],seconds=round(time.monotonic()-start,1))
def job(seed,arm):
 import traceback
 try:
  result=job_impl(seed,arm)
  write(P/'results'/f's{seed}_{arm}_JOB_STATUS.json',dict(status='SOLVER_COMPLETED',**result))
  return result
 except BaseException as exc:
  write(P/'results'/f's{seed}_{arm}_JOB_STATUS.json',dict(status='SIMULATOR_FAILURE',seed=seed,arm=arm,error=repr(exc),traceback=traceback.format_exc()))
  raise

def run():
 assert read(P/'checks/VALIDATION.json')['status']=='PASS'
 lock=read(P/'SOURCE_LOCK.json');assert lock['protocol']==sha(P/'PROTOCOL.json')
 for n,h in lock['binaries'].items():assert h==sha(P/'bin'/n)
 start=time.monotonic();print('Foreground pilot: 24 acquisitions, each followed by two tests; four workers.',flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  fs=[pool.submit(job,s,a) for s in SEEDS for a in ARMS]
  try:
   for i,f in enumerate(concurrent.futures.as_completed(fs),1):
    d=f.result();print(json.dumps(dict(done=i,total=24,elapsed=round(time.monotonic()-start),last=d)),flush=True)
    write(P/'STATUS.json',dict(status='FOREGROUND_RUNNING',completed=i,total=24,elapsed=time.monotonic()-start))
  except BaseException:
   for f in fs:f.cancel()
   write(P/'STATUS.json',dict(status='STOPPED_SIMULATOR_FAILURE',note='Inspect per-job statuses and stderr. Missing planned jobs remain not run, never excluded or replaced.'))
   raise
 write(P/'STATUS.json',dict(status='COMPLETED',training=24,evaluations=48,elapsed_seconds=time.monotonic()-start))
if __name__=='__main__':globals()[sys.argv[1]]()
