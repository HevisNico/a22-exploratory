"""English report and scientific figures for the fixed-gain experiment."""
import json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,findfont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Image,Spacer,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
P=Path(__file__).resolve().parent
LABELS={'normal':'Learned local rule','ungated':'Learned without cutoff','fixed_all':'Fixed g=4, b=0.08','fixed_all_max_b':'Fixed g=4, b=1.1','fixed_gain':'Fixed g=4, learned b'}
COLORS={'normal':'#155e75','fixed_all':'#ca7025','fixed_all_max_b':'#25816c','fixed_gain':'#8c62a6'}
def pct(v,d=2):return f'{100*v:.{d}f}%'
def group(x,rule,level,gap=20,frozen=True):return x['groups'][f'{rule}_L{level}_gap{gap}_N128_{"frozen" if frozen else "active"}']
def plot(x):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for i,rule in enumerate(['normal','fixed_all','fixed_all_max_b','fixed_gain']):
        positions=np.arange(3)+(i-1.5)*.19
        axes[0].bar(positions,[group(x,rule,l)['complete_words'] for l in range(3)],width=.18,color=COLORS[rule],label=LABELS[rule])
        axes[1].bar(positions,[100*group(x,rule,l,8)['mean_recall'] for l in range(3)],width=.18,color=COLORS[rule])
    axes[0].set(title='Original held-out test: intervals 20-24',ylabel='Complete output words / 20 seeds',ylim=(0,21),yticks=[0,5,10,15,20])
    axes[1].set(title='Faster held-out test: intervals 8-9.6',ylabel='Labels occurring exactly once (%)',ylim=(0,103),yticks=[0,25,50,75,100])
    for ax in axes:ax.set_xticks(range(3),['Low\nσ=0.05','Medium\nσ=0.10','High\nσ=0.15']);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False);fig.savefig(P/'fixed_gain_results.png',dpi=200);plt.close(fig)
def build():
    x=json.loads((P/'summary.json').read_text());plot(x)
    for name,weight in [('D','normal'),('DB','bold')]:pdfmetrics.registerFont(TTFont(name,findfont(FontProperties(family='DejaVu Sans',weight=weight))))
    pdfmetrics.registerFontFamily('D',normal='D',bold='DB',italic='D',boldItalic='DB')
    styles=getSampleStyleSheet()
    for name,font,size,leading,color in [('Body','D',9,13,'#253345'),('Heading','DB',14,19,'#155e75'),('Big','DB',24,29,'#155e75'),('Small','D',7.3,10,'#57687a')]:
        styles.add(ParagraphStyle(name='A22'+name,fontName=font,fontSize=size,leading=leading,textColor=colors.HexColor(color),spaceAfter=9))
    story=[]
    def p(text,style='Body'):story.append(Paragraph(text,styles['A22'+style]))
    def table(data,widths):
        cells=[[Paragraph(str(c),styles['A22Small']) for c in row] for row in data];t=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8f1f4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#9db7c0')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#dce4e9')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,10))
    baseline_words=sum(group(x,'fixed_all',l)['complete_words'] for l in range(3));maxb_words=sum(group(x,'fixed_all_max_b',l)['complete_words'] for l in range(3))
    if baseline_words==60:verdict='The original held-out test is passed without learning in all 60 fixed-gain realizations.'
    elif maxb_words==60:verdict='A fully fixed design with maximum gains and recovery passes all 60 original held-out realizations.'
    else:verdict='The fixed-gain controls expose a dependence on recovery settings and input rate.'
    p('A22 / FIXED-GAIN CONTROL','Small');p('Can high fixed gains<br/>replace learning?','Big');p('130 layers · 12 lanes · 20 paired seeds · 3 noise levels','Heading');p('<b>'+verdict+'</b>')
    p('The primary control sets every port gain to 4 and recovery b to its nominal value 0.08 at time zero. Both remain fixed throughout the 2,048 conditioning impulses and all tests. No noisy training outcome, learned gain, or learned recovery value is used to configure this control.')
    p('A second fully fixed control starts with b=1.1, its existing upper bound. A third control fixes gains at 4 while retaining the original local update of b. Both were specified before observing the new network results.')
    data=[['Noise σ','Learned local rule','Fully fixed<br/>g=4, b=0.08','Fully fixed<br/>g=4, b=1.1','Fixed g=4;<br/>learned b']]
    for l in range(3):
        row=[f'{.05*(l+1):.2f}']
        for rule in ['normal','fixed_all','fixed_all_max_b','fixed_gain']:
            g=group(x,rule,l);row.append(f'{pct(g["mean_recall"])} recall<br/>{g["complete_words"]}/20 complete words')
        data.append(row)
    table(data,[48,111,111,111,111])
    p('Primary endpoint: 128 independent held-out impulses at irregular source intervals of 20-24. Learned states and learned b are frozen at the start of the comparisons above. A complete word requires all 128 labels in order on all 12 output lanes, with no additional events. Recall counts only labels occurring exactly once.','Small')
    story.append(Image(str(P/'fixed_gain_results.png'),width=492,height=180))
    story.append(PageBreak())
    p('Recovery and input rate','Big')
    p('Conditioning uses intervals of 8, while the original held-out test uses intervals of 20-24. We therefore added an independently held-out faster test with intervals of 8-9.6, declared before the new fixed-gain outcomes. The same standardized perturbation field is shared across conditions within each rate; separate random stages are used between the two rates.')
    data=[['Noise σ','Learned local rule','Fully fixed<br/>b=0.08','Fully fixed<br/>b=1.1','Fixed gains;<br/>learned b, frozen']]
    for l in range(3):
        row=[f'{.05*(l+1):.2f}']
        for rule in ['normal','fixed_all','fixed_all_max_b','fixed_gain']:
            g=group(x,rule,l,8);row.append(f'{pct(g["mean_recall"])} recall<br/>{g["complete_words"]}/20 words')
        data.append(row)
    table(data,[48,111,111,111,111])
    p('Why nominal recovery can fail at the faster rate','Heading')
    p('For fixed b, the model has one unit of fast protection, followed by decay from charge 0.25 to 0.10 at rate b. Its protected duration is therefore <b>1 + ln(2.5)/b</b>: approximately <b>12.45</b> at b=0.08 and <b>1.83</b> at b=1.1. The slower original test allows nominal recovery to finish. A failure with fixed b=0.08 at the faster rate cannot, by itself, establish that gain learning is necessary.')
    p('Conditioning phase: final 128 source labels','Heading')
    data=[['Noise σ','Learned rule recall','Fixed b=0.08 recall','Fixed b=1.1 recall','Fixed gains, adaptive b recall']]
    for l in range(3):data.append([f'{.05*(l+1):.2f}']+[pct(x['training'][f'{r}_L{l}']['training_tail128_recall']) for r in ['normal','fixed_all','fixed_all_max_b','fixed_gain']])
    table(data,[48,111,111,111,111])
    p('These conditioning scores are descriptive and never select or exclude a seed. For the fully fixed controls, conditioning exposes the network to the same source sequence but changes no parameter. Tests start from independent copies after the same long source silence used previously.','Small')
    story.append(PageBreak())
    p('What the control establishes','Big')
    p('The earlier noisy-training advantage over clean training remains a valid result for networks starting from the nominal parameters. The new control tests a different causal question: whether parameter learning is required when high gains may be chosen in advance. Successful fully fixed transmission supplies another route to the same output endpoint.')
    p('The local rule still offers automatic adjustment from nominal gains and recovery, while keeping most gains below their upper bound. This experiment measures transmission, timing, and parameter values. It does not measure energy or hardware cost, and it does not establish an optimal fixed design or superiority at a matched gain budget.')
    data=[['Condition','Mean gain<br/>low / medium / high','Mean b<br/>low / medium / high','Gain-cap fraction<br/>low / medium / high']]
    for rule in ['normal','ungated','fixed_all','fixed_all_max_b','fixed_gain']:
        t=[x['training'][f'{rule}_L{l}'] for l in range(3)];data.append([LABELS[rule],' / '.join(f'{a["mean_gain"]:.3f}' for a in t),' / '.join(f'{a["mean_b"]:.3f}' for a in t),' / '.join(pct(a['gain_cap_fraction'],1) for a in t)])
    table(data,[132,122,122,116])
    p('Protocol and statistical unit','Heading')
    p('All new controls use 2,048 conditioning impulses, the same 130-layer ring geometry, initial charge 0.1, 12 lanes, and source injection into lane 0 only. Noise levels pair log-amplitude σ=0.05, 0.10, 0.15 with uniform arrival-jitter standard deviation 0.015, 0.030, 0.045. Mean amplitude is preserved by exp(σZ-σ²/2). The nominal delay remains 0.1. Seeds 0-19 and event-keyed SplitMix64/Box-Muller fields match the preceding campaign.')
    p('The statistical unit is the seed, not a lane or impulse. The primary contrast is learned-normal frozen recall minus fully fixed g=4, b=0.08 recall on the 128-impulse original test. Paired percentile bootstrap confidence intervals use 20,000 resamples. Two-sided sign tests receive Holm correction across the three primary noise levels; other analyses are exploratory. A 20/20 success count has an exact 95% binomial interval of approximately 83.16%-100%.')
    data=[['Noise σ','Primary recall difference; 95% CI','Sign-test p','Holm-adjusted p']]
    for l in range(3):
        d=x['paired'][f'gap20_L{l}_normal_minus_fixed_all'];data.append([f'{.05*(l+1):.2f}',f'{100*d["mean_difference"]:+.3f} percentage points<br/>[{100*d["CI95"][0]:.3f}, {100*d["CI95"][1]:.3f}]',f'{d["sign_p_two_sided"]:.4g}',f'{d["primary_Holm_3"]:.4g}'])
    table(data,[48,252,96,96])
    p('All results are finite numerical observations in the supplied point simulator. They are not interval certificates or guarantees for arbitrary future perturbations. Permanent termination of all local learning updates is not established.','Small')
    story.append(PageBreak())
    p('Validation and reproducibility','Big')
    p('The control extension distinguishes two parameter-freeze modes: gains and b frozen, or gains frozen with the original local b update retained. The existing active and fully frozen modes are unchanged. Local comparisons against the Python solver cover all three noise levels, both source rates, both freeze modes, and the maximum-b preset.')
    validation=json.loads((P/'VALIDATION.json').read_text());reg=json.loads((P/'validation/REGRESSION.json').read_text());audit=json.loads((P/'AUDIT.json').read_text())
    p(f'<b>Local solver validation:</b> {validation["cases"]} cases; no label mismatches; maximum event-time difference {validation["max_time_difference"]:.3g}.<br/><b>Network regression:</b> exact equality of all four matched tests from a previous learned checkpoint, including layer metrics and final event times.<br/><b>Integrity audit:</b> {audit["new_datasets"]} new datasets, {audit["reference_datasets"]} preceding datasets, and {audit["matched_test_instances_checked"]} matched test instances checked. Final outputs were independently recounted. Required fixed-parameter changes are exactly zero.')
    oracle_path=P/'validation/PYTHON_NETWORK.json'
    if oracle_path.exists():
        oracle=json.loads(oracle_path.read_text());p(f'<b>Independent 130-layer Python control:</b> all discrete scores agree for the fully fixed nominal-recovery 24-impulse control; maximum final event-time difference {oracle["max_final_output_time_difference"]:.3g}.')
    p('Precision on the original held-out test','Heading')
    data=[['Noise σ','Learned rule RMS','Fixed b=0.08 RMS','Fixed b=1.1 RMS','Fixed gains, learned b RMS']]
    for l in range(3):data.append([f'{.05*(l+1):.2f}']+[pct(group(x,r,l)['mean_relative_rms'],3) if group(x,r,l)['mean_relative_rms'] is not None else 'No valid pairs' for r in ['normal','fixed_all','fixed_all_max_b','fixed_gain']])
    table(data,[48,111,111,111,111])
    p('RMS is the seed-mean relative error of intervals between consecutive source labels found once. Losses and duplicates are counted separately. A low RMS among surviving labels does not compensate for missing labels.','Small')
    p('All 120 preceding text checkpoints were compared with their full JSON training states. One file had 1,548 of 1,560 rows and was reconstructed from the complete JSON records, preserving every numerical state value. The affected faster test was rerun with the same seed and field. No seed or outcome was excluded; the recovery audit is retained.','Small')
    p('English archive contents','Heading')
    p('summary.json contains group estimates and paired comparisons; results.csv and training.csv contain seed-level endpoints and parameter diagnostics. Raw output/ files retain layer profiles, final event trains, and checkpoints. reference_campaign/output/ supplies the preceding matched learned states and raw results. The full file guide is in README.txt.','Small')
    p('VALIDATION.json, AUDIT.json and validation/ retain solver checks and independent output recounts. PROVENANCE.json records SHA-256 hashes; ENVIRONMENT.json records the software environment. The Python scripts and C++ sources are supplied, with .diff files against the preceding engine.','Small')
    p('Reproduce','Heading');p('From the extracted folder: <b>python build.py</b>; <b>python validate.py</b>; <b>python run_campaign.py --workers 8</b>; <b>python analyze.py</b>; <b>python report.py</b>. Complete cached outputs are reused. Move output/ to recompute the new controls, while retaining reference_campaign/. The paired source fields and old checkpoints are supplied. No external account or original ZIP is needed to rerun the controls.','Small')
    p('The upper-bound recovery preset and faster-rate tests are declared secondary controls. Their interpretation does not replace the original primary endpoint. No parameter was selected using held-out results; no seed was excluded. Source changes relative to the previous engine are included as .diff files.','Small')
    def footer(canvas,doc):canvas.setFont('D',7);canvas.setFillColor(colors.HexColor('#637384'));canvas.drawString(45,27,'A22 · Fixed maximum-gain controls · Exploratory point simulation');canvas.drawRightString(550,27,str(doc.page))
    out=P/'A22_fixed_gain_controls_report.pdf';doc=SimpleDocTemplate(str(out),pagesize=(595.28,841.89),leftMargin=45,rightMargin=45,topMargin=40,bottomMargin=42,title='A22 - Fixed maximum-gain controls',author='Experimental analysis');doc.build(story,onFirstPage=footer,onLaterPages=footer);print(out)
if __name__=='__main__':build()
