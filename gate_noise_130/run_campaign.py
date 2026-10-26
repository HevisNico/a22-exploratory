"""Rebuild first: g++ -O3 -std=c++17 -ffp-contract=off network.cpp -o network.
Jobs are independent processes, with deterministic event-keyed random fields.
"""
import argparse, concurrent.futures, json, subprocess, time
from pathlib import Path
P=Path(__file__).resolve().parent
def job(seed,rule,level,clean=False):
    prefix=P/'output'/ (f'clean_test_{level}_{seed}' if clean else f'{rule}_{level}_{seed}')
    dest=prefix.with_suffix('.json')
    if dest.exists():
        try:
            if json.loads(dest.read_text()).get('status')=='OK_POINT_NOT_CERTIFIED':return {'name':prefix.name,'cached':True}
        except json.JSONDecodeError:pass
    start=time.monotonic()
    args=[str(P/'network'),str(seed),rule,str(.05*(level+1)),str(.015*(level+1)), '2048',str(prefix),str(P/'output/clean_training.states') if clean else '-',str(level)]
    result=subprocess.run(args,capture_output=True,text=True)
    record={'name':prefix.name,'seconds':round(time.monotonic()-start,3),'exit':result.returncode,'error':result.stderr}
    if result.returncode:raise RuntimeError(record)
    data=json.loads(dest.read_text());assert data['status']=='OK_POINT_NOT_CERTIFIED'
    return record
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);a=ap.parse_args()
    (P/'output').mkdir(exist_ok=True)
    clean=P/'output/clean_training.states'
    if not clean.exists():
        subprocess.run([str(P/'network'),'0','normal','0','0','2048',str(P/'output/clean_training'),'-','1'],check=True)
    jobs=[(seed,rule,level,False) for level in range(3) for seed in range(20) for rule in ['normal','ungated']]
    jobs += [(seed,'normal',level,True) for level in range(3) for seed in range(20)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(job,*args) for args in jobs]
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):
            record={'done':i,'total':len(jobs),**f.result()};print(json.dumps(record),flush=True)
