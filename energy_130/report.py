"""English report and exportable scientific figures, built from audited outputs."""
import base64,html,json,pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=pathlib.Path(__file__).resolve().parent
S=json.loads((P/'summary.json').read_text());A=json.loads((P/'AUDIT.json').read_text());V=json.loads((P/'VALIDATION.json').read_text())
assert not A['errors'] and V['status']=='PASS'
PAIRS={(p['comparison'],p['level']):p for p in S['paired_comparisons']}
GROUPS={(g['mode'],g['level'],g['condition']):g for g in S['groups']}
LEVELS={-1:'Quiet (one deterministic case)',0:'Low noise',1:'Medium noise',2:'High noise'}
NAMES={'same_state_gate_intervention':'Gate intervention: same learned state','acquisition_from_same_nominal_state':'Acquisition: same nominal start','trained_policy_test':'Test after each policy trained','one_acquisition_plus_one_test':'One acquisition + one test','secondary_frozen_gain_assignment':'Secondary: frozen gain assignment'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
fig,axs=plt.subplots(2,2,figsize=(12,8.5))
kinds=['same_state_gate_intervention','acquisition_from_same_nominal_state','one_acquisition_plus_one_test','secondary_frozen_gain_assignment']
for ax,kind in zip(axs.ravel(),kinds):
    for i,l in enumerate([0,1,2]):
        p=PAIRS[kind,l];v=p['relative_percent'];lo,hi=p['relative_percent_CI95'];ax.errorbar(v,i,xerr=[[max(0,v-lo)],[max(0,hi-v)]],fmt='o',capsize=5,color=['#2176ae','#218b78','#bb6b39'][i],markersize=7)
    ax.axvline(0,color='#718096',linewidth=1,linestyle='--');ax.set_yticks(range(3),['Low','Medium','High']);ax.invert_yaxis();ax.grid(axis='x',alpha=.15);ax.set_title(NAMES[kind],fontsize=11)
    ax.set_xlabel('Relative total work difference (%)\nNegative: gate on costs less' if kind!='secondary_frozen_gain_assignment' else 'Learned gains versus uniform gain 4 (%)\nNegative: learned gains cost less')
fig.suptitle('Different comparisons answer different questions',fontsize=16,y=.99)
fig.text(.5,.015,'20 paired network seeds per noise level; 95% paired bootstrap intervals. Original cost law unchanged.',ha='center',fontsize=10)
fig.tight_layout(rect=[0,.05,1,.96]);fig.savefig(P/'paired_energy_comparisons.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4.9))
for ax,key,title in [(axs[0],'gain_learning','Work spent changing log-gains'),(axs[1],'cap_fraction','Gains at cap after the test (%)')]:
    for j,c in enumerate(['gate_on','gate_off']):
        vals=[GROUPS['test',l,c]['means'][key]*(100 if key=='cap_fraction' else 1) for l in range(3)]
        ax.bar(np.arange(3)+(j-.5)*.33,vals,.32,label='Gate on' if j==0 else 'Gate off',color=['#2176ae','#bb6b39'][j])
    ax.set_xticks(range(3),['Low','Medium','High']);ax.set_title(title);ax.grid(axis='y',alpha=.15)
axs[0].set_ylabel('Model work units');axs[1].set_ylabel('Percent of all 4,680 gains')
fig.suptitle('Direct intervention from identical learned states',fontsize=15)
handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.93),ncol=2,frameon=False)
fig.tight_layout(rect=[0,0,1,.83]);fig.savefig(P/'gain_motion_and_saturation.png',dpi=180);plt.close(fig)

def table(headers,rows):
    return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+html.escape(str(x))+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def image(name):return '<img alt="'+name.replace('_',' ')+'" src="data:image/png;base64,'+base64.b64encode((P/name).read_bytes()).decode()+'">'
def pct(x):return f'{x:+.3f}%'
def ci(p):return f"[{p['relative_percent_CI95'][0]:+.3f}, {p['relative_percent_CI95'][1]:+.3f}]"
def verdict(p):
    lo,hi=p['relative_percent_CI95']
    if hi<0:return 'Gate on: lower total work in this sample.'
    if lo>0:return 'Gate on: higher total work in this sample.'
    return 'The paired interval includes zero.'
t='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>A22 — Corrected energy audit and matched rerun</title><style>body{font:16px/1.55 system-ui,sans-serif;color:#192b40;max-width:1120px;margin:40px auto;padding:0 24px;background:#fff}h1{font-size:35px;line-height:1.15;max-width:850px}h2{margin-top:40px;border-top:1px solid #dce5ec;padding-top:22px;font-size:23px}h3{font-size:18px}p{max-width:1000px}small,.muted{color:#596a7e}.note{background:#eef5fa;border-left:4px solid #2176ae;padding:16px 20px;margin:20px 0}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px;margin:18px 0}th,td{text-align:left;padding:11px 12px;border-bottom:1px solid #dce5ec;vertical-align:top}th{background:#eef3f7}img{width:100%;height:auto;margin:18px 0}code{background:#f1f4f7;padding:2px 5px}li{margin:8px 0}.eyebrow{color:#2176ae;letter-spacing:.08em;font-size:13px;font-weight:700}</style><body><div class="eyebrow">A22 · CORRECTED EXPERIMENTAL REPORT</div><h1>Energy, learning and the READY gate</h1><p class="muted">Matched interventions · 130 layers × 12 lanes · 20 seeds per noisy level · English reproducibility package</p>'''
t+='<div class="note"><b>What was corrected.</b> The previous frozen-gain comparison was overinterpreted as a direct gate test. This rerun separates those questions, measures acquisition on all twenty seeds, independently reconstructs the physical dynamics for local validation, and integrates pump input from its own rate. No physical cost term was changed to favor either outcome.</div>'
t+='<h2>Direct gate intervention: the primary result</h2><p>Both branches load exactly the same normally trained checkpoint and start the test with the same gains, b, relaxed q and E=100. Both can learn. The sole intervention removes the READY condition from gain learning in the gate-off branch. Recovery learning retains its original law in both. Later differences in b or downstream traffic are consequences of this intervention, not differences in starting conditions.</p>'
t+=table(['Noise','Work: on minus off','Paired 95% interval (%)','Complete words: on / off','Label recall: on / off'],[[LEVELS[l],pct(PAIRS['same_state_gate_intervention',l]['relative_percent']),ci(PAIRS['same_state_gate_intervention',l]),f"{PAIRS['same_state_gate_intervention',l]['full_words_on']}/20 · {PAIRS['same_state_gate_intervention',l]['full_words_off']}/20",f"{100*PAIRS['same_state_gate_intervention',l]['recall_on']:.4f}% / {100*PAIRS['same_state_gate_intervention',l]['recall_off']:.4f}%"] for l in range(3)])
t+='<p>Relative differences are ratios of the two mean total costs, with pairing preserved in bootstrap resampling. Complete-word success means all 128 labels are recovered exactly once and in order on every output lane. Cost and fidelity are separate endpoints; this report does not assume equal delivered service.</p>'+image('paired_energy_comparisons.png')
t+='<h2>Acquisition and the complete measured sequence</h2><p>Both learning rules were rerun from the same nominal state on 2,048 training pulses. Each resulting network then received the same 128-pulse held-out test. The lifecycle total below includes that one acquisition and that one test. It is not an extrapolation to unlimited future use. Quiet is one deterministic example, not twenty independent observations.</p>'
rows=[]
for l in [-1,0,1,2]:
    a=PAIRS['acquisition_from_same_nominal_state',l];b=PAIRS['one_acquisition_plus_one_test',l];c=PAIRS['trained_policy_test',l]
    rows.append([LEVELS[l],pct(a['relative_percent']),pct(c['relative_percent']),pct(b['relative_percent']),ci(b) if l>=0 else 'Single example',f"{b['full_words_on']}/{b['n']} · {b['full_words_off']}/{b['n']}"])
t+=table(['Noise','Acquisition','Own-trained test','Acquisition + test','Total 95% interval (%)','Test complete words: on / off'],rows)
t+='<p>These comparisons estimate the total consequence of using each learning policy. Changes in both gains and b are legitimate effects of the policy. They cannot be attributed to gain size alone. Full-training recall, final-128-pulse training recall, and interval distortion are retained separately in metrics.csv.</p>'
t+='<h2>Gain motion and saturation</h2>'+image('gain_motion_and_saturation.png')
rows=[]
for l in [-1,0,1,2]:
    a=GROUPS['train',l,'gate_on']['means'];b=GROUPS['train',l,'gate_off']['means'];c=GROUPS['test',l,'gate_on']['means'];d=GROUPS['test',l,'gate_off']['means']
    rows.append([LEVELS[l],f"{100*a['cap_fraction']:.2f}% / {100*b['cap_fraction']:.2f}%",f"{100*c['cap_fraction']:.2f}% / {100*d['cap_fraction']:.2f}%",f"{c['gain_learning']:.3f} / {d['gain_learning']:.3f}"])
t+=table(['Noise','At cap after acquisition: on / off','At cap after matched test: on / off','Gain-motion work in matched test: on / off'],rows)
t+='<p>Saturation here means reaching the numerical gain cap 4, counted over all 4,680 stored gains, including ports with little or no input. Saturation avoidance, reduced gain motion, reduced total work and transmission quality are distinct claims. A finite campaign cannot prove universal necessity of the gate.</p>'
t+='<h3>Where the matched-test cost difference comes from</h3><p>The following accounting separates main-cell work, auxiliary work and parameter movement. Positive entries mean the gate-on branch spends more. A reduction in the gain-learning term can coexist with a larger total cost.</p>'
rows=[]
for l in range(3):
    p=PAIRS['same_state_gate_intervention',l];d=p['mean_component_delta']
    rows.append([LEVELS[l],f"{sum(d[k] for k in ['main_admission','main_fast','main_slow']):+,.2f}",f"{sum(d[k] for k in ['aux_admission','aux_mark','aux_silent','aux_error']):+,.2f}",f"{d['gain_learning']:+,.2f}",f"{d['b_learning']:+,.2f}",f"{p['mean_delta']:+,.2f}"])
t+=table(['Noise','Main work','Auxiliary work','Gain movement','b movement','Total difference'],rows)
t+='<h2>Secondary frozen comparison</h2><p>This reproduces the earlier gain-assignment comparison: freeze learned gains and b, then substitute uniform gain 4 in the control while retaining the same b at each cell. It measures test-time use of static configurations, not the direct effect of switching the learning gate.</p>'
t+=table(['Noise','Learned versus uniform 4 work','Paired 95% interval (%)','Complete words: learned / uniform'],[[LEVELS[l],pct(PAIRS['secondary_frozen_gain_assignment',l]['relative_percent']),ci(PAIRS['secondary_frozen_gain_assignment',l]),f"{PAIRS['secondary_frozen_gain_assignment',l]['full_words_on']}/20 · {PAIRS['secondary_frozen_gain_assignment',l]['full_words_off']}/20"] for l in range(3)])
t+='<h2>Energy law and reserve scope</h2><p><code>dE/dt = 10(100 − E) − W</code>. W includes admitted main current, main fast drain, constant slow-phase power 1.1, admitted auxiliary current, the three auxiliary drains, actual log-gain movement and actual b movement. The source specifies unit coefficients. Values are model work units, not calibrated joules.</p><p>Static large gains have no maintenance penalty under this law. Stronger input may close admission earlier. The cost of creating an externally prescribed uniform gain, the external pulse source and any unspecified hardware overhead are not invented or charged. Integrating the reserve does not by itself supply a microscopic energy model.</p>'
t+=f'<p>Every cell starts at E=100 and must pass a finite-path positive-bound check. Across this campaign the smallest continuous lower bound was <b>{A["minimum_continuous_E_bound"]:.6f}</b>, and the smallest event-sampled reserve was <b>{A["minimum_sampled_E"]:.6f}</b>. The sampled minimum is not claimed to be the exact continuous minimum. These runs do not reach depletion, and the production solver still refuses paths whose bound cannot guarantee E&gt;0. No E=0 behavior or resource-limited necessity is demonstrated.</p>'
t+='<p>After training, the long quiet interval relaxes q and E without changing gains or b. Total work is integrated through the completion of main and auxiliary responses. Pump input during the measured window is integrated separately; adding final replenishment restores E to its initial value and makes total pump supply equal total work. The raw pump-window total is not substituted for the work endpoint.</p>'
t+='<h2>Validation and audit</h2>'
t+=table(['Check','Result and scope'],[['Independent physical oracle',f"{V['cases']} local cases; integrates q, m, z, b, E, all work terms and pump from raw inputs, with its own threshold events. No C++ work coefficients or switch times are reused."],['Maximum oracle discrepancies',f"Work component: {V['max_errors']['work']:.3g}; reserve: {V['max_errors']['reserve']:.3g}; output-event time: {V['max_errors']['event_time']:.3g}."],['Coverage','Gain cap, b cap, partial gating, frozen parameters, no main firing, no input, and several pulse spacings.'],['Matched initial states',f"{A['matched_checkpoint_pairs']} direct-intervention pairs verified by exact checkpoint SHA-256."],['Whole campaign',f"{A['dataset_count']} datasets; {len(A['errors'])} audit errors. Component sums, section masses, parameter endpoints, raw output words and reserve bounds checked."],['Pump balance',f"Pump now integrated from 10(100−E), not defined by the balance identity. Largest network residual: {A['max_pump_balance_absolute_error']:.3g} model units."],['Limits','Numerical point simulations and local independent cross-checks; not a certified interval replay or a proof covering every hybrid trajectory.']])
if (P/'REGRESSION.json').exists():
    rr=json.loads((P/'REGRESSION.json').read_text());t+=f'<p>Historical regression: {rr["checks"]} comparisons with previously saved outputs; {len(rr["errors"])} differences beyond the specified tolerances. Agreement is a regression check, not a substitute for the independent oracle.</p>'
t+='<h2>Reproduce and inspect</h2><p>The archive includes the pinned model reference and licenses, C++ solver, independent Python oracle, raw training/test events, terminal states, protocol, audit, paired summaries, CSV metrics and figures. See README.txt for commands. Source: <a href="https://github.com/HevisNico/a22-interval-replay">HevisNico/a22-interval-replay</a>, commit <code>22294781127aa47628bb8a3270d5c5a758c31729</code>, reference sections 2–4.</p><p>Bootstrap intervals use 20 network seeds per noisy level, not individual lanes or pulses. They are exploratory and unadjusted for multiple comparisons. The 130-layer noisy campaign is an extension of the reference setting; it is not covered merely by citing the source’s nominal interval results.</p></body></html>'
(P/'report.html').write_text(t)
print('English report and two figures written.')
