"""Check experiment integrity, input assumptions, and final-score consistency."""
import ctypes as ct,json,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
def run():
    problems=[];datasets=0;tests=0;quiet=math.inf;worst_frozen_z=worst_frozen_b=0.
    for path in (P/'output').glob('*.json'):
        x=json.loads(path.read_text())
        if x['status']!='OK_POINT_NOT_CERTIFIED':problems.append([path.name,'status'])
        if x['training_N']!=2048:problems.append([path.name,'duration'])
        if x['training']:
            if len(x['training'])!=130:problems.append([path.name,'training depth'])
            for l in x['training']:
                if len(l['cells'])!=12:problems.append([path.name,'training width'])
                for c in l['cells']:
                    s=c['state']
                    if s['phase']!=0 or any(z>math.log(4)+1e-12 for z in s['z']) or not .08<=s['b']<=1.1+1e-12:problems.append([path.name,'invalid learned state'])
        for t in x['tests']:
            tests+=1
            if len(t['layers'])!=130:problems.append([path.name,'test depth'])
            for l in t['layers']:
                m=l['metric'];quiet=min(quiet,l['minimum_quiet'])
                if m['expected']!=12*t['pulses']:problems.append([path.name,'denominator'])
                if m['full_network_word'] and not (m['recall']==1 and m['events']==m['expected'] and m['order_violations']==m['duplicates']==m['ambiguous']==0):problems.append([path.name,'full word inconsistency'])
                if t['frozen']:
                    worst_frozen_z=max(worst_frozen_z,abs(l['delta_z']));worst_frozen_b=max(worst_frozen_b,abs(l['delta_b']))
            # Independently recount each final output lane's complete ordered word.
            full=0;found=0
            from collections import Counter
            for row in t['output_events']:
                labels=[v[1] for v in row];counts=Counter(labels)
                found+=sum(counts[1000000+i]==1 for i in range(t['pulses']))
                full+=labels==list(range(1000000,1000000+t['pulses']))
            if full!=t['layers'][-1]['metric']['complete_lanes'] or found!=t['layers'][-1]['metric']['found']:problems.append([path.name,'independent output recount'])
        datasets+=1
    assert quiet>0 and worst_frozen_z==worst_frozen_b==0 and not problems,problems
    result={'status':'PASS','datasets_including_clean_training':datasets,'test_instances_including_controls':tests,'minimum_quiet_time':quiet,'frozen_max_log_gain_change':worst_frozen_z,'frozen_max_b_change':worst_frozen_b,'independent_final_output_recounts':'all matched','problems':problems}
    (P/'AUDIT.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':print(json.dumps(run(),indent=2))
