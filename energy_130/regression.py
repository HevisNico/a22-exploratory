"""Compare regenerated states/results with the previous campaign, when available."""
import json,pathlib,numpy as np
P=pathlib.Path(__file__).resolve().parent;OLD=P.parent/'energy_experiment'
def main():
    if not OLD.exists():
        print('Previous campaign not available; optional historical regression skipped.');return
    checks=[];errors=[]
    for f in sorted((P/'training').glob('*.json')):
        d=json.loads(f.read_text());l=d['level'];s=d['seed'];rule='normal' if d['condition']=='gate_on' else 'ungated'
        old=OLD/'training'/f'L-1_s0_{rule}.json.states' if l==-1 else OLD/'inputs'/f'{rule}_{l}_{s}.states'
        if old.exists():
            a=np.loadtxt(str(f)+'.states');b=np.loadtxt(old);delta=float(np.max(np.abs(a-b)));checks.append(dict(file=f.name,kind='trained states',max_absolute_difference=delta,bitwise_equal=bool(np.array_equal(a,b))))
            if delta>1e-8:errors.append(checks[-1])
    mapping={'gate_on':'normal_active','trained_off':'ungated_active','normal_frozen':'normal_frozen','uniform4_frozen':'uniform4_learned_b'}
    for f in sorted((P/'results').glob('*.json')):
        d=json.loads(f.read_text());c=d['condition']
        if c not in mapping:continue
        old=OLD/'results'/f"L{d['level']}_s{d['seed']}_{mapping[c]}.json"
        if not old.exists():continue
        b=json.loads(old.read_text());same=d['output_events']==b['output_events'];relative=abs(d['energy']['work_total']-b['energy']['work_total'])/max(1,b['energy']['work_total'])
        checks.append(dict(file=f.name,kind='held-out events and work',exact_output_events=same,relative_work_difference=relative))
        if not same or relative>1e-10:errors.append(checks[-1])
    result=dict(checks=len(checks),errors=errors,details=checks,note='Historical agreement is a regression check, not independent model validation. The independent ODE oracle is in VALIDATION.json.')
    (P/'REGRESSION.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='details'}))
    if errors:raise RuntimeError('historical regression differs; investigate before claiming equivalence')
if __name__=='__main__':main()
