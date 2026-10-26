"""Matched-duration clean training; held-out noisy tests matched by seed."""
import concurrent.futures,json,os,time,traceback
from pathlib import Path
import native_run as sim
P=Path(__file__).parent;OUT=P/'output_native'
def clean_training(N):
    path=OUT/f'clean_training_{N}.json';lock=path.with_suffix('.lock')
    owner=False
    while not path.exists():
        try:
            fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd);owner=True
        except FileExistsError:time.sleep(.5);continue
        try:
            training,states,counts=sim.train(0,N,sigma=0.,jitter=0.)
            tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(training,separators=(',',':')));tmp.replace(path)
        finally:lock.unlink(missing_ok=True)
        break
    d=json.loads(path.read_text());states={};counts={(0,0):N}
    for c in d['cells']:
        key=c['layer'],c['lane'];states[key]=c['end_state'];counts[key]=c['training_count']
    return d,states,counts
def run(seed):
    dest=OUT/f'matched_clean_{seed}.json'
    if dest.exists():return {'seed':seed,'cached':True}
    start=time.monotonic()
    try:
        primary=json.loads((OUT/f'seed_{seed}.json').read_text());N=primary['training_N']
        training,states,counts=clean_training(N)
        tests=[sim.test(seed,N,states,counts,stage,count,False,.1,.03) for stage,count in [('primary',24),('long',128)]]
        result={'status':'OK_POINT_NOT_CERTIFIED','name':f'matched_clean_{seed}','condition':'clean_training','seed':seed,'quiet':False,'sigma':.1,'jitter':.03,'training_sigma':0.,'training_jitter':0.,'training_N':N,'prepared_observed':training['prepared_observed'],'tests':tests,'seconds':time.monotonic()-start}
    except Exception as e:result={'status':'UNSUPPORTED_OR_ERROR','name':f'matched_clean_{seed}','seed':seed,'error':repr(e),'traceback':traceback.format_exc()}
    tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(result,separators=(',',':')));tmp.replace(dest)
    return {'seed':seed,'status':result['status'],'training_N':result.get('training_N'),'seconds':result.get('seconds'),'error':result.get('error')}
if __name__=='__main__':
    pending=set(range(20));active={};done=0
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as ex:
        while pending or active:
            for seed in sorted(pending):
                if len(active)>=2:break
                if (OUT/f'seed_{seed}.json').exists():active[ex.submit(run,seed)]=seed;pending.remove(seed)
            for future in list(active):
                if future.done():done+=1;print(json.dumps({'done':done,**future.result()}),flush=True);del active[future]
            if pending or active:time.sleep(.5)
