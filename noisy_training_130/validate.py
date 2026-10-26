import json,math
from pathlib import Path
from run import train,test,TEST_LABEL
P=Path(__file__).parent
if __name__=='__main__':
    training,states,counts=train(0,128)
    old=json.loads((P/'oracle_128/all_normal_0.json').read_text())
    mismatches=[];gainerr=[]
    for c in old['cells']:
        key=(c['layer'],c['lane']);st=states[key]
        if c['training_count']!=counts[key]:mismatches.append(['training',*key])
        gainerr.extend(abs(a-b) for a,b in zip(st['g'],c['before']['g']))
    dates=[];test_checks=[]
    for freeze,name in [(False,'all_normal_0'),(True,'frozen_learned_0')]:
        result=test(0,128,states,counts,freeze=freeze)
        reference=json.loads((P/'oracle_128'/f'{name}.json').read_text());by={(c['layer'],c['lane']):c for c in reference['cells']}
        for c in result['cells']:
            key=(c['layer'],c['lane']);ref=by[key]
            gainerr.extend(abs(a-b) for a,b in zip(c['after']['g'],ref['after']['g']))
            if 'events' in c:
                actual=[(t+4096.,None if label is None else label-TEST_LABEL+128) for t,label in c['events']]
                expected=ref['probe_events']
                if [l for t,l in actual]!=[l for t,l in expected]:mismatches.append(['probe_labels',freeze,*key])
                if len(actual)==len(expected):dates.extend(abs(a[0]-b[0]) for a,b in zip(actual,expected))
        for layer in result['layers']:
            expected=sum(len(c['probe_events']) for c in reference['cells'] if c['layer']==layer['layer'])
            if layer['events']!=expected:mismatches.append(['layer_probe_count',freeze,layer['layer']])
        test_checks.append({'freeze':freeze,'final_recall':result['layers'][-1]['recall'],'minimum_quiet_time':result['minimum_quiet_time']})
    result={'status':'PASS' if not mismatches and max(gainerr)<1e-7 and max(dates)<1e-7 else 'FAIL','mismatches':mismatches,'max_gain_error':max(gainerr),'max_probe_date_error':max(dates),'checks':test_checks,'method':'training/test split compared with full uninterrupted 128-pulse noisy simulation, seed 0, both adaptive and frozen test'}
    (P/'SPLIT_VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));assert result['status']=='PASS'
