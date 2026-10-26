"""Validate passive provenance and regress unchanged physical trajectories."""
import concurrent.futures,hashlib,json,pathlib,subprocess
from run import job
P=pathlib.Path(__file__).resolve().parent
if __name__=='__main__':
    unit=subprocess.run([str(P/'validation/unit')],capture_output=True,text=True,check=True).stdout
    planned=[(1,0,'learned','clean'),(1,0,'uniform4','clean'),(2,0,'uniform4','lateral_100'),(-1,0,'uniform2','noise_only'),(0,0,'directional','wrong_lane')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for x in pool.map(lambda a:job(*a),planned):print(x,flush=True)
    checks=[];historical_available=(P.parent/'energy_corrected/results').exists()
    for condition,oldc in [('learned','normal_frozen'),('uniform4','uniform4_frozen')]:
        if not historical_available:continue
        new=json.loads((P/'results'/f'L1_s0_{condition}_clean.json').read_text());old=json.loads((P.parent/'energy_corrected/results'/f'L1_s0_{oldc}.json').read_text())
        events=[[[e[0],e[1]] for e in lane] for lane in new['output_events']]
        assert events==old['output_events']
        assert new['score']['true_found']==old['layers'][-1]['metric']['found']
        error=abs(new['energy']['work_total']-old['energy']['work_total'])/old['energy']['work_total'];assert error<1e-12
        checks.append(dict(condition=condition,exact_event_regression=True,relative_energy_error=error))
    for args in planned:
        l,s,c,t=args;d=json.loads((P/'results'/f'L{l}_s{s}_{c}_{t}.json').read_text())
        assert d['score']['unattributed_events']==0
        assert d['energy']['work_components']['gain_learning']==0 and d['energy']['work_components']['b_learning']==0
        assert d['injection_timing']['violations']==0
    r=dict(status='PASS',binary_sha256=hashlib.sha256((P/'experiment').read_bytes()).hexdigest(),unit_output=unit,regressions=checks,historical_regression_available=historical_available,pilot_datasets=len(planned),scope='Same physical kernel as corrected energy campaign, with passive ancestry metadata; previous independent 25-case state-equation validation retained in reference/. Not a new independent general hybrid proof.')
    (P/'VALIDATION.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
