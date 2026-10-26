import json
from pathlib import Path
from run import run
P=Path(__file__).parent
if __name__=='__main__':
    c={'name':'recheck_reference_all_normal_0','rule':'normal','noise_phase':'all','seed':0,'reference_solver':True}
    print(run(c),flush=True)
    ref=json.loads((P/'output'/f"{c['name']}.json").read_text());new=json.loads((P/'output/all_normal_0.json').read_text())
    assert ref['status']==new['status']=='OK_POINT_NOT_CERTIFIED'
    dates=[];gains=[];mismatches=[]
    for a,b in zip(ref['cells'],new['cells']):
        if a['training_count']!=b['training_count'] or [l for t,l in a['probe_events']]!=[l for t,l in b['probe_events']]:mismatches.append([a['layer'],a['lane']])
        if len(a['probe_events'])==len(b['probe_events']):dates.extend(abs(x[0]-y[0]) for x,y in zip(a['probe_events'],b['probe_events']))
        for stage in ['before','after']:gains.extend(abs(x-y) for x,y in zip(a[stage]['g'],b[stage]['g']))
    result={'cell_count':len(ref['cells']),'count_or_label_mismatches':mismatches,'max_probe_date_error':max(dates,default=0.),'max_gain_error':max(gains,default=0.),'status':'PASS' if not mismatches and max(dates,default=0)<1e-7 and max(gains,default=0)<1e-7 else 'FAIL'}
    (P/'REFERENCE_RECHECK.json').write_text(json.dumps(result,indent=2));print(result)
    assert result['status']=='PASS'
