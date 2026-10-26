import concurrent.futures, subprocess, json, time, hashlib, pathlib
P=pathlib.Path(__file__).resolve().parent; SOURCE=P/'inputs'
def job(seed,level,cap,rule):
 checkpoint=SOURCE/('clean_training.states' if level==-1 else f'normal_{level}_{seed}.states')
 dest=P/'results'/f'L{level}_seed{seed}_cap{cap}_{rule}.json'
 if dest.exists():
  try:
   if json.loads(dest.read_text())['status']=='OK_POINT_NOT_CERTIFIED':return {'file':dest.name,'cached':True}
  except Exception:pass
 t=time.monotonic();sigma=0 if level==-1 else .05*(level+1);jitter=0 if level==-1 else .015*(level+1)
 r=subprocess.run([str(P/'experiment'),str(checkpoint),str(seed),str(sigma),str(jitter),str(cap),rule,str(dest),'0'],capture_output=True,text=True)
 if r.returncode:raise RuntimeError((dest.name,r.stderr))
 return {'file':dest.name,'seconds':round(time.monotonic()-t,3)}
if __name__=='__main__':
 jobs=[(seed,l,cap,rule) for l in [-1,0,1,2] for seed in (range(1) if l==-1 else range(20)) for cap in [4,8,16] for rule in ['normal','ungated']]
 jobs +=[(seed,l,16,'restore') for l in [-1,0,1,2] for seed in (range(1) if l==-1 else range(20))]
 with concurrent.futures.ProcessPoolExecutor(max_workers=8) as pool:
  futures=[pool.submit(job,*j) for j in jobs]
  for i,f in enumerate(concurrent.futures.as_completed(futures),1):print(json.dumps({'done':i,'total':len(jobs),**f.result()}),flush=True)
