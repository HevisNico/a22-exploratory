import pathlib,json,collections,csv,hashlib,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=pathlib.Path(__file__).resolve().parent
raw=[];audit={'datasets':0,'errors':[],'shuffle_checks':0,'all_final_events_recounted':0}
for f in sorted((P/'results').glob('*.json')):
 try:d=json.loads(f.read_text())
 except json.JSONDecodeError:continue
 if 'condition' not in d:continue
 c=d['condition'];m=d['layers'][-1]['metric'];audit['datasets']+=1
 if d['max_log_gain_change']!=0:audit['errors'].append([f.name,'gain changed'])
 if c['bmode']!='adaptive' and d['max_b_change']!=0:audit['errors'].append([f.name,'b changed'])
 # Recount complete ordered words and exact-label recall directly from output events.
 found=full=0
 for train in d['output_events']:
  counts=collections.Counter(x[1] for x in train);found+=sum(counts[2000000+i]==1 for i in range(128))
  full+=len(train)==128 and [x[1] for x in train]==list(range(2000000,2000128))
 if found!=m['found'] or (full==12)!=m['full_network_word']:audit['errors'].append([f.name,'event recount'])
 audit['all_final_events_recounted']+=1
 if c['kind'] not in ['uniform','learned']:
  check=d['shuffle_validation']
  if not all(check.get(k) for k in ['global_gain_multiset_preserved','layer_gain_multisets_preserved','learned_b_preserved']):audit['errors'].append([f.name,'shuffle failed'])
  audit['shuffle_checks']+=1
 raw.append({**c,'name':f.stem,**m,'max_b_change':d['max_b_change'],'final_mean_b':d['final_mean_b']})
with (P/'metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(raw[0]));w.writeheader();w.writerows(raw)
# Aggregate repeated shuffle draws within each seed before uncertainty estimates.
byseed=collections.defaultdict(list)
for r in raw:byseed[r['level'],r['kind'],r['bmode'],r['gain'],r['seed']].append(r)
seedrows=[]
for key,rs in sorted(byseed.items()):
 l,kind,bmode,g,seed=key
 seedrows.append({'level':l,'kind':kind,'bmode':bmode,'gain':g,'seed':seed,'draws':len(rs),'recall':np.mean([r['recall'] for r in rs]),'full_word_rate':np.mean([r['full_network_word'] for r in rs]),'duplicates':np.mean([r['duplicates'] for r in rs]),'relative_rms':np.mean([r['relative_rms'] for r in rs if r['relative_rms'] is not None]) if any(r['relative_rms'] is not None for r in rs) else None})
groups=collections.defaultdict(list)
for r in seedrows:groups[r['level'],r['kind'],r['bmode'],r['gain']].append(r)
rng=np.random.default_rng(20261025);summary=[]
for (l,kind,bmode,g),rs in sorted(groups.items()):
 out={'level':l,'kind':kind,'bmode':bmode,'gain':g,'network_seeds':len(rs),'draws_per_seed':rs[0]['draws']}
 for key in ['recall','full_word_rate','duplicates']:
  v=np.array([r[key] for r in rs]);boot=v[rng.integers(len(v),size=(20000,len(v)))].mean(axis=1)
  out[key]={'mean':float(v.mean()),'min':float(v.min()),'max':float(v.max()),'seed_bootstrap_CI95':np.quantile(boot,[.025,.975]).tolist()}
 out['full_words']=int(sum(r['full_word_rate']*r['draws'] for r in rs));out['realizations']=sum(r['draws'] for r in rs);out['seeds_with_all_words_complete']=int(sum(r['full_word_rate']==1 for r in rs))
 summary.append(out)
paired=[]
base={(r['level'],r['seed']):r for r in seedrows if r['kind']=='learned'}
for (l,kind,bmode,g),rs in sorted(groups.items()):
 if l<0 or kind=='learned':continue
 if any((l,r['seed']) not in base for r in rs):continue
 out={'level':l,'kind':kind,'bmode':bmode,'gain':g,'direction':'condition minus learned frozen baseline','network_seeds':len(rs)}
 for key in ['recall','full_word_rate']:
  v=np.array([r[key]-base[l,r['seed']][key] for r in rs]);boot=v[rng.integers(len(v),size=(20000,len(v)))].mean(axis=1)
  out[key]={'mean_difference':float(v.mean()),'paired_seed_bootstrap_CI95':np.quantile(boot,[.025,.975]).tolist()}
 paired.append(out)
(P/'summary.json').write_text(json.dumps({'groups':summary,'paired_exploratory':paired},indent=2));(P/'AUDIT.json').write_text(json.dumps(audit,indent=2))
if audit['errors']:raise RuntimeError(audit)
fig,axs=plt.subplots(1,2,figsize=(11,4.6));colors={-1:'#777777',0:'#2274a5',1:'#23967f',2:'#c75b39'};levels={-1:'No noise',0:'Low noise',1:'Medium noise',2:'High noise'}
for l in [-1,0,1,2]:
 ss=sorted([s for s in summary if s['kind']=='uniform' and s['bmode']=='adaptive' and s['level']==l],key=lambda s:s['gain'])
 if ss:
  for ax,key in zip(axs,['recall','full_word_rate']):ax.plot([s['gain'] for s in ss],[s[key]['mean'] for s in ss],marker='o',markersize=3,color=colors[l],label=levels[l])
for ax,title in zip(axs,['Exact-label recall at layer 130','Complete ordered word on all 12 lanes']):ax.set(title=title,xlabel='Uniform fixed gain',ylabel='Fraction',ylim=(-.03,1.03));ax.grid(alpha=.2)
axs[0].legend(fontsize=8);fig.suptitle('Gains fixed from t=0; b starts at 0.08 and follows its original learning rule');fig.tight_layout();fig.savefig(P/'uniform_gain_sweep.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4.6));kinds=['learned','within_layer','within_layer_port','tail_within_layer'];names=['Learned\nunchanged','Shuffle\nwithin layer','Shuffle\nlayer + port','Shuffle tail\nlayers 7–130']
for idx,l in enumerate([0,1,2]):
 for ax,key in zip(axs,['recall','full_word_rate']):
  ss=[next((s for s in summary if s['level']==l and s['kind']==kind),None) for kind in kinds]
  x=np.arange(4)+(idx-1)*.23;heights=[s[key]['mean'] if s else np.nan for s in ss];ax.bar(x,heights,width=.22,color=colors[l],label=levels[l])
for ax,title in zip(axs,['Exact-label recall at layer 130','Complete-word rate (two shuffles per seed)']):ax.set_xticks(range(4),names,fontsize=8);ax.set(title=title,ylabel='Fraction',ylim=(0,1.08));ax.grid(axis='y',alpha=.2)
axs[0].legend(fontsize=8);fig.suptitle('Learned b retained; gains and b frozen; 20 paired network seeds per noise level');fig.tight_layout();fig.savefig(P/'learned_gain_shuffles.png',dpi=180);plt.close(fig)
print(json.dumps(audit))
