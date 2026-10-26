import concurrent.futures,json
from pathlib import Path
from run_experiments import run
if __name__=='__main__':
    cases=json.loads(Path(__file__).with_name('selected_cases.json').read_text())
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as ex:
        for i,r in enumerate(ex.map(run,cases),1):print(json.dumps({'done':i,'total':len(cases),**r}),flush=True)
