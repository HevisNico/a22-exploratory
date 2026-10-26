import concurrent.futures,subprocess,pathlib,json,hashlib,time,tempfile
import numpy as np
P=pathlib.Path(__file__).resolve().parent
GRID=[.3,.6,.9,1.2,1.4,1.6,1.8,2.,2.5,3.,4.]
MODES=['within_layer','within_layer_port','tail_within_layer']
def jobs():
 out=[]
 for level in [-1,0,1,2]:
  for seed in (range(1) if level==-1 else range(20)):
   for g in GRID:out.append(dict(level=level,seed=seed,kind='uniform',gain=g,bmode='adaptive',draw=-1))
   for g in (GRID if level==-1 else [1.6,2.,3.,4.]):out.append(dict(level=level,seed=seed,kind='uniform',gain=g,bmode='fixed_high',draw=-1))
   for g in [2.,4.]:out.append(dict(level=level,seed=seed,kind='uniform',gain=g,bmode='fixed_nominal',draw=-1))
   out.append(dict(level=level,seed=seed,kind='learned',gain=0,bmode='learned_frozen',draw=-1))
   for mode in MODES:
    for draw in range(2):out.append(dict(level=level,seed=seed,kind=mode,gain=0,bmode='learned_frozen',draw=draw))
 return out
def name(j):return f"L{j['level']}_s{j['seed']}_{j['kind']}_{j['bmode']}_g{j['gain']:g}_d{j['draw']}"
def job(j):
 dest=P/'results'/(name(j)+'.json')
 if dest.exists():
  try:
   if json.loads(dest.read_text()).get('status')=='OK_POINT_NOT_CERTIFIED':return {'name':name(j),'cached':True}
  except Exception:pass
 t=time.monotonic();seed=j['seed'];level=j['level'];kind=j['kind'];checkpoint='-';tmp=None;check={}
 try:
  if kind!='uniform':
   src=P/'inputs'/('clean_training.states' if level==-1 else f'normal_{level}_{seed}.states');checkpoint=str(src)
   if kind!='learned':
    state=np.loadtxt(src);assert state.shape==(1560,7)
    old=state[:,:3].copy();perm=np.arange(4680);rng=np.random.default_rng(np.random.SeedSequence([20261025,level+1,seed,j['draw'],MODES.index(kind)]))
    for layer in range(130):
     if kind=='tail_within_layer' and layer<6:continue
     if kind=='within_layer_port':
      for port in range(3):
       ix=np.arange(layer*36+port,(layer+1)*36,3);perm[ix]=rng.permutation(ix)
     else:
      ix=np.arange(layer*36,(layer+1)*36);perm[ix]=rng.permutation(ix)
    new=old.ravel()[perm].reshape(1560,3);state[:,:3]=new
    assert np.array_equal(np.sort(old.ravel()),np.sort(new.ravel()))
    assert all(np.array_equal(np.sort(old.reshape(130,36)[i]),np.sort(new.reshape(130,36)[i])) for i in range(130))
    check={'global_gain_multiset_preserved':True,'layer_gain_multisets_preserved':True,'learned_b_preserved':True,'original_gain_hash':hashlib.sha256(old.tobytes()).hexdigest(),'shuffled_gain_hash':hashlib.sha256(new.tobytes()).hexdigest()}
    if kind=='tail_within_layer':assert np.array_equal(old[:72],new[:72]);check['first_six_layers_unchanged']=True
    if kind=='within_layer_port':
     assert all(np.array_equal(np.sort(old.reshape(130,12,3)[i,:,p]),np.sort(new.reshape(130,12,3)[i,:,p])) for i in range(130) for p in range(3));check['layer_port_multisets_preserved']=True
    permfile=P/'permutations'/(name(j)+'.npz');np.savez_compressed(permfile,indices=perm)
    with tempfile.NamedTemporaryFile(mode='w',dir=P/'temporary',suffix='.states',delete=False) as f:np.savetxt(f,state,fmt='%.17g');tmp=pathlib.Path(f.name)
    checkpoint=str(tmp)
  args=[str(P/'control'),checkpoint,str(seed),str(level),j['bmode'],str(j['gain']),str(dest),'128']
  r=subprocess.run(args,capture_output=True,text=True)
  if r.returncode:raise RuntimeError((name(j),r.stderr))
  d=json.loads(dest.read_text());d['condition']=j;d['shuffle_validation']=check;d['seconds']=time.monotonic()-t
  update=dest.with_suffix('.meta.tmp');update.write_text(json.dumps(d,separators=(',',':')));update.replace(dest)
  return {'name':name(j),'seconds':round(d['seconds'],3)}
 finally:
  if tmp:tmp.unlink(missing_ok=True)
if __name__=='__main__':
 for sub in ['results','permutations','temporary']:(P/sub).mkdir(exist_ok=True)
 js=jobs();errors=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=8) as pool:
  fs={pool.submit(job,j):j for j in js}
  for i,f in enumerate(concurrent.futures.as_completed(fs),1):
   try:r=f.result()
   except Exception as e:r={'error':str(e),'condition':fs[f]};errors.append(r)
   print(json.dumps({'done':i,'total':len(js),**r}),flush=True)
 (P/'RUN_ERRORS.json').write_text(json.dumps(errors,indent=2))
 if errors:raise SystemExit(1)
