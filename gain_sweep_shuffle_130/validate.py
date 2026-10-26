import pathlib,subprocess,json
P=pathlib.Path(__file__).resolve().parent
checks=[]
cases=[('-',0,-1,'fixed_high',1.6),('-',0,0,'fixed_high',1.6),('-',0,1,'adaptive',4), (str(P/'inputs/normal_1_0.states'),0,1,'learned_frozen',0)]
for i,args in enumerate(cases):
 records=[]
 for executable,label in [('control','instrumented'),('validation/reference_control','reference')]:
  dest=P/'validation'/f'{label}_{i}.json';subprocess.run([str(P/executable),*map(str,args),str(dest),'128'],check=True);records.append(json.loads(dest.read_text()))
 assert records[0]==records[1],i
 checks.append({'case':i,'arguments':args,'comparison':'exact full JSON identity against reference kernel'})
# Active b and frozen gains must be exercised separately.
dest=P/'validation/active_b_fixed_gain.json';subprocess.run([str(P/'control'),'-','0','1','adaptive','2',str(dest),'128'],check=True)
d=json.loads(dest.read_text());assert d['max_log_gain_change']==0 and d['max_b_change']>0
checks.append({'case':'separate_freezes','max_log_gain_change':d['max_log_gain_change'],'max_b_change':d['max_b_change']})
(P/'VALIDATION.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks))
