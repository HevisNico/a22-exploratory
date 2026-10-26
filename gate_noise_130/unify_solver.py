"""Recompute initial bisection jobs with the final solver; retain audit copies."""
from pathlib import Path
import concurrent.futures, json, shutil, subprocess
P=Path(__file__).resolve().parent
def run(rule,seed):
    name=f'{rule}_0_{seed}';dest=P/'output'/name;archive=P/'validation/bisection_original';archive.mkdir(exist_ok=True)
    shutil.copy2(dest.with_suffix('.json'),archive/(name+'.json'))
    prefix=P/'validation'/('uniform_'+name)
    if rule=='normal' and seed==0:
        shutil.copy2(P/'validation/root_long.json',prefix.with_suffix('.json'));shutil.copy2(P/'validation/root_long.states',prefix.with_suffix('.states'))
    else:
        subprocess.run([str(P/'network'),str(seed),rule,'.05','.015','2048',str(prefix),'-','0'],check=True,capture_output=True)
    x=json.loads(prefix.with_suffix('.json').read_text());assert x['status']=='OK_POINT_NOT_CERTIFIED'
    prefix.with_suffix('.json').replace(dest.with_suffix('.json'));prefix.with_suffix('.states').replace(dest.with_suffix('.states'))
    return name
if __name__=='__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as ex:
        fs=[ex.submit(run,rule,seed) for rule in ['normal','ungated'] for seed in range(4)]
        for f in concurrent.futures.as_completed(fs):print(f.result(),flush=True)
