import json, pathlib, collections, csv, math, hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=pathlib.Path(__file__).resolve().parent
rows=[];datasets={};audit={'errors':[],'datasets':0,'restoration_identical_first_block':0}
for f in sorted((P/'results').glob('*.json')):
 try:d=json.loads(f.read_text())
 except json.JSONDecodeError:continue
 datasets[f.name]=d;audit['datasets']+=1
 level=-1 if d['sigma']==0 else round(d['sigma']/.05)-1
 for b in d['blocks']:
  requested=b['requested_ready']+b['requested_protected'];expected=.6*3*(b['count']+sum(x['metric']['events'] for x in b['layers'][:-1]))
  if abs(requested-expected)>1e-5:audit['errors'].append([f.name,b['cumulative_pulses'],'requested charge',requested,expected])
  eligible=requested if b['ungated'] else b['requested_ready']
  if not -1e-8<=b['delta_z']<=eligible+1e-5:audit['errors'].append([f.name,'ineligible update'])
  rows.append({'level':level,'seed':d['seed'],'cap':d['cap'],'rule':d['rule'],'pulses':b['cumulative_pulses'],'block_count':b['count'],'delta_z':b['delta_z'],'requested_ready':b['requested_ready'],'requested_protected':b['requested_protected'],**b['terminal'],**{k:b['layers'][-1]['metric'][k] for k in ['recall','full_network_word','duplicates','relative_rms']}})
for name,d in datasets.items():
 if d['rule']=='restore':
  other=datasets.get(name.replace('_restore','_ungated'))
  if other is not None:
   if d['blocks'][0]!=other['blocks'][0]:audit['errors'].append([name,'different first block'])
   else:audit['restoration_identical_first_block']+=1
with (P/'metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
groups={}
for r in rows:groups.setdefault((r['level'],r['cap'],r['rule'],r['pulses']),[]).append(r)
summary=[]
for (level,cap,rule,pulses),rs in sorted(groups.items()):
 out={'level':level,'cap':cap,'rule':rule,'pulses':pulses,'n':len(rs)}
 for k in ['delta_z','requested_ready','requested_protected','mean_gain','cap_fraction','recall']:
  v=[r[k] for r in rs];out[k]={'mean':float(np.mean(v)),'min':min(v),'max':max(v)}
 out['full_words']=sum(r['full_network_word'] for r in rs);out['gains_still_moving']=sum(r['delta_z']>1e-8 for r in rs)
 summary.append(out)
# Paired seed bootstrap for final mean gain and recall; exploratory, no success inference from ties.
rng=np.random.default_rng(20261025);paired=[]
for level in [0,1,2]:
 for cap in [4,8,16]:
  aa={r['seed']:r for r in rows if r['level']==level and r['cap']==cap and r['rule']=='normal' and r['pulses']==512};bb={r['seed']:r for r in rows if r['level']==level and r['cap']==cap and r['rule']=='ungated' and r['pulses']==512}
  seeds=sorted(aa.keys()&bb.keys())
  if not seeds:continue
  for key in ['mean_gain','recall','cap_fraction']:
   v=np.array([bb[i][key]-aa[i][key] for i in seeds]);boots=v[rng.integers(len(v),size=(20000,len(v)))].mean(axis=1)
   paired.append({'level':level,'cap':cap,'endpoint':key,'direction':'ungated minus normal','n':len(v),'mean_difference':float(v.mean()),'CI95':np.quantile(boots,[.025,.975]).tolist()})
(P/'summary.json').write_text(json.dumps({'groups':summary,'paired_exploratory':paired},indent=2));(P/'AUDIT.json').write_text(json.dumps(audit,indent=2))
if audit['errors']:raise RuntimeError(audit)
colors={4:'#4169a1',8:'#26958e',16:'#bd6451'}
fig,axs=plt.subplots(2,2,figsize=(11,7),sharex=True)
for ax,level,title in zip(axs.flat,[-1,0,1,2],['Sans bruit (1 état)','Bruit faible (20 graines)','Bruit moyen (20 graines)','Bruit fort (20 graines)']):
 for cap in [4,8,16]:
  for rule,style in [('normal','-'),('ungated','--')]:
   ss=sorted([s for s in summary if s['level']==level and s['cap']==cap and s['rule']==rule],key=lambda x:x['pulses']);ax.plot([0]+[s['pulses'] for s in ss],[np.mean([d['initial']['mean_gain'] for d in datasets.values() if (d['sigma']==0 if level==-1 else abs(d['sigma']-.05*(level+1))<1e-8) and d['cap']==cap and d['rule']==rule])]+[s['mean_gain']['mean'] for s in ss],style,color=colors[cap],label=f'Plafond {cap}, '+('coupure' if rule=='normal' else 'sans coupure'))
 ss=sorted([s for s in summary if s['level']==level and s['cap']==16 and s['rule']=='restore'],key=lambda x:x['pulses'])
 if ss:ax.plot([s['pulses'] for s in ss],[s['mean_gain']['mean'] for s in ss],':',color='black',label='Coupure rétablie après 1 pulse')
 ax.set_title(title);ax.set_ylabel('Gain moyen');ax.grid(alpha=.2)
for ax in axs[-1]:ax.set_xlabel('Impulsions supplémentaires (blocs avec repos)')
handles,labels=axs.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=8);fig.tight_layout(rect=[0,.13,1,1]);fig.savefig(P/'gains.png',dpi=180);plt.close(fig)
print(json.dumps(audit));print('Final groups:')
for s in summary:
 if s['pulses']==512:print(json.dumps(s))
