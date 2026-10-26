import sys,json,math,statistics,csv,collections
from pilot import P,SEEDS,ARMS,read,write
from scoring import match_times,audit_physics

def metrics(d):
 dates=[0.]
 for i in range(127):dates.append(dates[-1]+[20,22,21,24,20,23][i%6])
 present=purepresent=unique=dups=other=events=complete=order=0;errors=[]
 for lane in d['output_events']:
  occurrences={i:[] for i in range(128)};tags=set()
  for k,e in enumerate(lane):
   tags.update(i for i in e[2] if 0<=i<128)
   if len(e[2])==1 and 0<=e[2][0]<128:occurrences[e[2][0]].append(k)
   else:other+=1
  present+=len(tags);purepresent+=sum(bool(v) for v in occurrences.values())
  ids=[e[2][0] for e in lane if len(e[2])==1 and 0<=e[2][0]<128]
  reversals=sum(b<a for a,b in zip(ids,ids[1:]));order+=reversals
  unique+=sum(len(v)==1 for v in occurrences.values()) if not reversals else 0
  dups+=sum(max(0,len(v)-1) for v in occurrences.values());events+=len(lane)
  complete+=len(lane)==128 and not reversals and all(len(v)==1 for v in occurrences.values())
  for i in range(127):
   if len(occurrences[i])==len(occurrences[i+1])==1:
    observed=lane[occurrences[i+1][0]][0]-lane[occurrences[i][0]][0]
    gap=dates[i+1]-dates[i];errors.append((observed-gap)/gap)
 return dict(source_tag_presence=present/1536,pure_source_presence=purepresent/1536,once_only_ordered_coverage=unique/1536,
  complete_lanes=complete,complete_word=complete==12,events=events,pure_source_duplicate_occurrences=dups,
  other_events=other,order_reversals=order,timing_valid_pairs=len(errors),timing_expected_pairs=1524,
  relative_interval_rms=math.sqrt(statistics.mean(e*e for e in errors)) if errors else None,
  max_abs_relative_interval_error=max(map(abs,errors)) if errors else None,work=d['energy']['work_total'])

def paired(a,b):
 added=removed=0
 for ref,test in zip(a['output_events'],b['output_events']):
  pairs=match_times([x[0] for x in ref],[x[0] for x in test],2)
  added+=len(test)-len(pairs);removed+=len(ref)-len(pairs)
 return dict(added_events=added,removed_events=removed)

def main():
 assert read(P/'STATUS.json')['status']=='COMPLETED'
 rows=[];ps=[];training=[]
 for seed in SEEDS:
  for arm in ARMS:
   t=read(P/'results'/f's{seed}_{arm}_train.json');trainok=t['final_training_metric']['full_network_word']
   training.append(dict(seed=seed,arm=arm,training_word=trainok,training_metric=t['final_training_metric']))
   docs={mode:read(P/'results'/f's{seed}_{arm}_{mode}.json') for mode in ['baseline','mixed']}
   for mode,d in docs.items():
    audit_physics(d);assert d['_provenance']['field_sha256']==t['_provenance']['field_sha256']
    rows.append(dict(seed=seed,arm=arm,mode=mode,training_word=trainok,solver_status='SOLVER_COMPLETED',**metrics(d)))
   ps.append(dict(seed=seed,arm=arm,**paired(docs['baseline'],docs['mixed'])))
 groups=[]
 for arm in ARMS:
  for mode in ['baseline','mixed']:
   rr=[r for r in rows if r['arm']==arm and r['mode']==mode]
   pp=[x for x in ps if x['arm']==arm]
   timing=[r['relative_interval_rms'] for r in rr if r['relative_interval_rms'] is not None]
   groups.append(dict(arm=arm,mode=mode,n=6,training_word_seeds=sum(r['training_word'] for r in rr),complete_word_seeds=sum(r['complete_word'] for r in rr),
    mean_once_only_coverage=statistics.mean(r['once_only_ordered_coverage'] for r in rr),
    mean_pure_source_presence=statistics.mean(r['pure_source_presence'] for r in rr),
    mean_duplicate_occurrences=statistics.mean(r['pure_source_duplicate_occurrences'] for r in rr),mean_other_events=statistics.mean(r['other_events'] for r in rr),
    mean_relative_interval_rms=statistics.mean(timing) if timing else None,timing_networks_with_valid_pairs=len(timing),timing_valid_pairs=sum(r['timing_valid_pairs'] for r in rr),
    max_abs_relative_interval_error=max((r['max_abs_relative_interval_error'] for r in rr if r['max_abs_relative_interval_error'] is not None),default=None),
    mean_decoy_added=statistics.mean(x['added_events'] for x in pp),mean_decoy_removed=statistics.mean(x['removed_events'] for x in pp)))
 by={(r['seed'],r['arm'],r['mode']):r for r in rows};contrasts=[]
 for mode in ['baseline','mixed']:
  for outcome in ['once_only_ordered_coverage','pure_source_duplicate_occurrences','other_events','complete_word']:
   for seed in SEEDS:
    nq=by[seed,'nominal_quiet',mode][outcome];nn=by[seed,'nominal_noisy',mode][outcome];uq=by[seed,'uncertain_quiet',mode][outcome];un=by[seed,'uncertain_noisy',mode][outcome]
    contrasts.append(dict(seed=seed,mode=mode,outcome=outcome,uncertainty_effect_quiet=uq-nq,uncertainty_effect_noisy=un-nn,interaction=(un-uq)-(nn-nq)))
 write(P/'PER_SEED.json',rows);write(P/'PAIRED_DECOY.json',ps);write(P/'TRAINING_OUTCOMES.json',training);write(P/'PAIRED_FACTORIAL_CONTRASTS.json',contrasts)
 summary=dict(status='EXPLORATORY_JOINT_PILOT_COMPLETED',groups=groups,simulator_failures=0,planned_acquisitions=24,completed_acquisitions=24,completed_evaluations=48,
  caveats=['Six fixed heterogeneous physical draws, epsilon=1e-4, low link noise only. No coverage of the full parameter box or proof for every noise realization.',
  'Every failed acquisition is retained. These aggregate results never condition on training success.',
  'Nominal quiet networks are physically identical across the six seeds; six logical reference rows do not provide six independent nominal-quiet devices.',
  'Quiet/noisy factor changes acquisition AND test noise; it is a total regime effect, not isolation of test-time susceptibility.',
  'Same latent link-noise field is used for paired nominal/uncertain conditions; different physical trajectories can consume different downstream keys.',
  'No initial-state uncertainty is included. Main constants a, kappa, r, r_m, b_max and pump stay nominal.',
  'Timing RMS excludes invalid adjacent-source pairs; pair coverage and transmission failures are reported alongside it.',
  'Passive tags are not complete residual-charge causal histories. Added timing events can include displacements.',
  'No independent inferential confirmation, necessity comparison, hybrid comparison or lifecycle energy superiority is claimed.'])
 write(P/'SUMMARY.json',summary)
 for filename,data in [('PER_SEED.csv',rows),('PAIRED_DECOY.csv',ps),('PAIRED_FACTORIAL_CONTRASTS.csv',contrasts)]:
  with (P/filename).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 lines=['A22 — JOINT PARAMETER UNCERTAINTY AND LINK-NOISE PILOT','',
 'Status: completed exploratory pilot. Physical parameters are sampled once per device and reused in acquisition and both tests.',
 'All 24 acquisitions and all 48 evaluations completed; simulator failures: 0. No failed model transmission is excluded.',
 'Six seeds (3000–3005), four paired acquisition/test regimes, 2048 acquisition pulses, 128 evaluation pulses, layer 130 with 12 lanes.',
 'Uncertainty: independent uniform relative +/-1e-4 on C, L_m, L_s, L_e and M, separately per cell and port. Same field in quiet/noisy uncertain arms.',
 'Noise: sigma_log_amplitude=.05, jitter_sd=.015 and mean link delay=.1. Paired nominal/uncertain arms share latent keys; acquisition stage 0 and test stage 8001 are disjoint.',
 '', 'arm | mode | acquisition words /6 | test words /6 | once-only coverage | mean relative interval RMS | mean decoy additions / removals']
 for g in groups:
  err='undefined' if g['mean_relative_interval_rms'] is None else f"{g['mean_relative_interval_rms']:.6%}"
  lines.append(f"{g['arm']} | {g['mode']} | {g['training_word_seeds']}/6 | {g['complete_word_seeds']}/6 | {g['mean_once_only_coverage']:.6%} | {err} | {g['mean_decoy_added']:.3f} / {g['mean_decoy_removed']:.3f}")
 lines+=['','LIMITS',*summary['caveats'],'','The stored physical fields, source locks, checkpoints, raw outputs, per-seed metrics and independent ODE checks accompany these results. No simulation continues after this pilot.']
 (P/'REPORT.txt').write_text('\n'.join(lines)+'\n');print('\n'.join(lines),flush=True)
if __name__=='__main__':main()
