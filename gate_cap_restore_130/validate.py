import json,subprocess,pathlib,math
P=pathlib.Path(__file__).resolve().parent;src=P/'inputs';out=P/'validation';out.mkdir(exist_ok=True)
results=[]
for seed in [0,1]:
 for rule in ['normal','ungated']:
  target=out/f'{rule}_{seed}.json'
  subprocess.run([str(P/'experiment'),str(src/f'normal_1_{seed}.states'),str(seed),'.1','.03','4',rule,str(target),'1'],check=True)
  # The archived ungated tests use different learned states, so run reference implementation on the same normal checkpoint separately.
  data=json.loads(target.read_text())
  if rule=='normal':
   old=json.loads((src/f'normal_1_{seed}.json').read_text())
   test=next(x for x in old['tests'] if x['level']==1 and x['pulses']==128 and not x['frozen'])
   block=data['blocks'][0]
   assert block['events']==test['output_events']
   for a,b in zip(block['layers'],test['layers']):assert a['metric']==b['metric']
   assert abs(block['delta_z']-sum(x['delta_z'] for x in test['layers']))<1e-9
   results.append({'seed':seed,'normal_cap4_archived_128':'EXACT_EVENTS_AND_ALL_LAYER_METRICS'})
# Compare amended kernel with original at cap4 on the same checkpoints, including ungated.
orig=P/'reference_src';orig.mkdir(exist_ok=True)
(orig/'point_cell.cpp').write_text((P/'src/original_point_cell.cpp').read_text()+'\nstatic double GAIN_CAP=4.;\n')
for name in ['common.cpp','experiment.cpp']:(orig/name).write_text((P/'src'/name).read_text())
subprocess.run(['g++','-O3','-std=c++17','-ffp-contract=off',str(orig/'experiment.cpp'),'-o',str(out/'reference')],check=True)
for seed in [0,1]:
 for rule in ['normal','ungated']:
  target=out/f'reference_{rule}_{seed}.json'
  subprocess.run([str(out/'reference'),str(src/f'normal_1_{seed}.states'),str(seed),'.1','.03','4',rule,str(target),'1'],check=True)
  a=json.loads(target.read_text())['blocks'][0];b=json.loads((out/f'{rule}_{seed}.json').read_text())['blocks'][0]
  for key in ['events','layers','delta_z','delta_b','terminal']:assert a[key]==b[key],key
  results.append({'seed':seed,'rule':rule,'original_kernel_cap4':'EXACT'})
(P/'VALIDATION.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
