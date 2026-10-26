"""Fixed maximum gains from t=0, and matched held-out rate controls."""
import argparse,concurrent.futures,json,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parent;PREVIOUS=P/'reference_campaign' if (P/'reference_campaign').exists() else P.parent/'experiment_coupure'
def job(seed,rule,level,gap=20):
    name=f'{rule}_L{level}_S{seed}_gap{gap}';prefix=P/'output'/name;dest=prefix.with_suffix('.json')
    if dest.exists():
        try:
            if json.loads(dest.read_text()).get('status')=='OK_POINT_NOT_CERTIFIED':return {'name':name,'cached':True}
        except json.JSONDecodeError:pass
    checkpoint='-'
    if gap==8:
        if rule in ['normal','ungated']:checkpoint=str(PREVIOUS/'output'/f'{rule}_{level}_{seed}.states')
        else:checkpoint=str(P/'output'/f'{rule}_L{level}_S{seed}_gap20.states')
    start=time.monotonic()
    result=subprocess.run([str(P/'network'),str(seed),rule,str(.05*(level+1)),str(.015*(level+1)),'2048',str(prefix),checkpoint,str(level),str(gap)],capture_output=True,text=True)
    if result.returncode:raise RuntimeError({'name':name,'error':result.stderr,'exit':result.returncode})
    x=json.loads(dest.read_text());assert x['status']=='OK_POINT_NOT_CERTIFIED'
    return {'name':name,'seconds':round(time.monotonic()-start,3)}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);a=ap.parse_args();(P/'output').mkdir(exist_ok=True)
    # Finish preparation files before dependent faster evaluations.
    phases=[[(s,r,l,20) for l in range(3) for s in range(20) for r in ['fixed_all','fixed_all_max_b','fixed_gain']],[(s,r,l,8) for l in range(3) for s in range(20) for r in ['fixed_all','fixed_all_max_b','fixed_gain','normal','ungated']]]
    for phase,jobs in enumerate(phases,1):
        with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
            fs=[pool.submit(job,*args) for args in jobs]
            for i,f in enumerate(concurrent.futures.as_completed(fs),1):
                record={'phase':phase,'done':i,'total':len(jobs),**f.result()}
                # One atomic file per record avoids a long shared output stream.
                tmp=P/'output'/('progress_'+record['name']+'.json.tmp');tmp.write_text(json.dumps(record));tmp.replace(tmp.with_suffix(''))
                print(json.dumps(record),flush=True)
