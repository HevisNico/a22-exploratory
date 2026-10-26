import collections,hashlib,html,json,platform,zipfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import main
P=Path(__file__).parent
NAMES={'all_normal':'Règle normale, bruit dès entraînement','all_none':'Sans apprentissage','all_ungated':'Apprentissage autorisé sous protection','probe_normal':'Règle normale, bruit seulement au test','frozen_learned':'Appris sous bruit puis figé au test'}
COLORS=['#176b87','#777777','#c25832','#8a6798','#42735e']
def fmt(x,m=1):return '—' if x is None else f'{x*m:.3g}'
def report():
    summary,layers=main();groups=summary['groups'];rows=summary['runs'];by={r['name']:r for r in rows}
    for group in NAMES:assert groups[group]['n']==20,(group,groups[group]['n'])
    assert not summary['unsupported']
    fig,axes=plt.subplots(2,2,figsize=(13,8.8));fig.patch.set_facecolor('#faf9f5')
    for (prefix,label),color in zip(NAMES.items(),COLORS):
        names=[r['name'] for r in rows if r['name'].startswith(prefix+'_')]
        curves=np.array([[m['recall']*100 for m in layers[name]] for name in names]);x=np.arange(1,131)
        axes[0,0].plot(x,curves.mean(axis=0),label=label,color=color,lw=1.6)
        axes[0,0].fill_between(x,curves.min(axis=0),curves.max(axis=0),alpha=.1,color=color)
    axes[0,0].set(title='Transmission en fonction de la profondeur',xlabel='Couche',ylabel='Impulsions retrouvées (%)',ylim=(-2,103));axes[0,0].legend(fontsize=7)
    for i,(prefix,label) in enumerate(NAMES.items()):
        v=[r['recall']*100 for r in rows if r['name'].startswith(prefix+'_')]
        axes[0,1].scatter(i+np.linspace(-.16,.16,len(v)),v,color=COLORS[i],s=25,alpha=.8)
        axes[0,1].plot([i-.22,i+.22],[np.mean(v)]*2,color='black',lw=2)
    short=['Normale\nbruit dès début','Sans\napprentissage','Sans coupure\nsous protection','Bruit seulement\nau test','Figé après\napprentissage']
    axes[0,1].set_xticks(range(5),short,fontsize=8);axes[0,1].set(title='Couche 130 — vingt graines par condition',ylabel='Impulsions retrouvées (%)',ylim=(-3,103))
    for key,label,color in [('all_normal','Normale sous bruit','#176b87'),('all_ungated','Sans coupure sous bruit','#c25832')]:
        names=[r['name'] for r in rows if r['name'].startswith(key+'_')]
        vals=np.array([[m['training_events']/12 for m in layers[name]] for name in names]);axes[1,0].plot(x,vals.mean(axis=0),color=color,label=label)
    for name,label,style in [('quiet_normal','Normale sans bruit','--'),('quiet_ungated','Sans coupure sans bruit',':')]:
        axes[1,0].plot(x,[m['training_events']/12 for m in layers[name]],style,label=label,color='#333333')
    axes[1,0].set(title='Propagation des 128 impulsions d’entraînement',xlabel='Couche',ylabel='Émissions d’entraînement par voie (moyenne)');axes[1,0].legend(fontsize=8)
    for pos,layer in enumerate([18,80,130]):
        vals=[]
        for prefix in NAMES:
            names=[r['name'] for r in rows if r['name'].startswith(prefix+'_')]
            vals.append(np.mean([layers[name][layer-1]['recall']*100 for name in names]))
        axes[1,1].bar(np.arange(5)+(pos-1)*.25,vals,width=.24,label=f'Couche {layer}')
    axes[1,1].set_xticks(range(5),short,fontsize=8);axes[1,1].set(title='Un résultat à 18 couches ne suffit pas',ylabel='Impulsions retrouvées (%)',ylim=(0,105));axes[1,1].legend(fontsize=8)
    for a in axes.ravel():a.grid(axis='y',alpha=.2);a.set_axisbelow(True)
    fig.suptitle('A22 — ablations appariées, 130 couches, 20 graines',fontsize=16)
    fig.text(.5,.005,'Bruit : σ log-charge = 0,10 ; gigue uniforme d’écart-type 0,03 ; 128 pulses d’entraînement puis 24 pulses de test.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.025,1,.96]);fig.savefig(P/'resultats.png',dpi=170);plt.close(fig)
    tab='<table><tr><th>Condition</th><th>Graines</th><th>Impulsions retrouvées à 130</th><th>Graines avec une émission</th><th>Mot complet sur les 12 voies</th><th>Erreur relative RMS*</th></tr>'
    for key,label in NAMES.items():
        g=groups[key];tab+=f"<tr><td>{label}</td><td>{g['n']}</td><td>{fmt(g['mean_recall'],100)} % (min {fmt(g['min_recall'],100)} ; max {fmt(g['max_recall'],100)})</td><td>{g['any_output_seeds']} / {g['n']}</td><td>{g['full_network_word_seeds']} / {g['n']}</td><td>{fmt(g['mean_relative_rms'],100)} %</td></tr>"
    tab+='</table><p>* L’erreur ne concerne que les paires d’étiquettes source consécutives retrouvées une fois. Elle ne compte pas les impulsions perdues. Un tiret signifie qu’aucune paire ne permet cette mesure.</p>'
    quiet='<table><tr><th>Contrôle sans bruit</th><th>Impulsions retrouvées à 130</th><th>Émissions de test</th><th>Émissions d’entraînement à 130</th><th>Voies avec mot complet</th></tr>'
    for key,label in [('quiet_normal','Normale'),('quiet_none','Sans apprentissage'),('quiet_ungated','Apprentissage sous protection')]:
        r=by[key];quiet+=f"<tr><td>{label}</td><td>{fmt(r['recall'],100)} %</td><td>{r['total_events']}</td><td>{r['training_events']}</td><td>{r['complete_lanes']} / 12</td></tr>"
    quiet+='</table>'
    indiv='<table><tr><th>Condition</th><th>Graine</th><th>Fraction retrouvée à 130</th><th>Émissions à 130</th><th>Première couche sans émission de test</th><th>Première couche sans entraînement</th></tr>'
    for r in rows:
        indiv+=f"<tr><td>{html.escape(r['name'])}</td><td>{r['seed']}</td><td>{fmt(r['recall'],100)} %</td><td>{r['total_events']}</td><td>{r['first_zero_test_layer'] or '—'}</td><td>{r['first_zero_training_layer'] or '—'}</td></tr>"
    indiv+='</table>'
    conclusion='<h2>Interprétation</h2><p><b>L’affirmation forte n’est pas confirmée à ce niveau de bruit.</b> La règle normale avec bruit dès l’entraînement retrouve seulement 1,37 % des impulsions à 130 couches, contre 54,20 % quand l’apprentissage reste actif sous protection. Cette dernière condition transmet davantage dans les vingt comparaisons appariées, mais ne conserve jamais le mot complet. On ne peut donc pas attribuer ici une robustesse profonde à la nécessité de la coupure pendant la protection.</p><p>L’apprentissage bruité fait légèrement mieux que l’apprentissage propre suivi de bruit au test (1,37 % contre 0 %), ce qui reste très loin d’une transmission robuste. La suppression complète de l’apprentissage empêche même l’amorçage dans le contrôle sans bruit.</p>'
    for key,label in [('all_normal','Règle normale avec bruit dès entraînement'),('all_ungated','Apprentissage autorisé sous protection')]:
        rs=[r for r in rows if r['name'].startswith(key+'_')]
        zero=sum(r['training_events']==0 for r in rs)
        conclusion+=f'<p>{label} : dans {zero} réalisations sur 20, aucune impulsion d’entraînement n’atteint la couche 130. Il faut donc distinguer l’installation du régime et sa robustesse une fois appris. Un échec à cette profondeur avec seulement 128 pulses ne démontre pas que le même milieu déjà appris échouerait, ni qu’un entraînement plus long suffirait.</p>'
    uncertainty=''
    for key,label in NAMES.items():
        g=groups[key];ci=g['any_output_probability_exact_CI95'];cw=g['full_word_probability_exact_CI95']
        uncertainty+=f"<p>{label} : intervalle exact à 95 % pour la probabilité d’au moins une émission à 130 [{fmt(ci[0],100)} %, {fmt(ci[1],100)} %] ; pour un mot complet sur les 12 voies [{fmt(cw[0],100)} %, {fmt(cw[1],100)} %].</p>"
    body=f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>A22 — ablations et bruit pendant l’apprentissage</title><style>body{{max-width:1150px;margin:35px auto;padding:0 25px;font:16px/1.55 system-ui;background:#faf9f5;color:#172e39}}h1,h2{{color:#13546c}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:20px 0}}th,td{{padding:8px;border-bottom:1px solid #ccd5d7;text-align:left}}th{{background:#e5eef0}}img{{width:100%}}code{{background:#e5eef0;padding:2px 4px}}.box{{padding:15px 20px;border-left:4px solid #c25832;background:white}}pre{{white-space:pre-wrap;font-size:12px}}</style>
<h1>A22 — ablations et apprentissage bruité à 130 couches</h1><p>100 réalisations principales (cinq conditions × vingt graines), trois contrôles sans bruit, et un rejeu de contrôle avec le solveur antérieur. Simulateur ponctuel fourni, étendu ; aucun moteur certifié importé.</p>
<div class="box"><b>Portée du test.</b> Il teste le bruit de charge à σ=0,10 et la gigue à 0,03, pour l’entraînement de 128 impulsions fourni. Il ne teste pas toutes les intensités de bruit, un entraînement arbitrairement long ni toutes les réalisations. Les conclusions à 18 couches ne sont pas extrapolées à 130.</div>
<h2>Résultats mesurés</h2>{tab}<img src="resultats.png" alt="Ablations et courbes de profondeur"><p>Aux premières couches, toutes les voies ne sont pas encore accessibles depuis la source : la montée initiale des courbes reflète l’élargissement spatial du front.</p>
{conclusion}<h2>Les contrôles sans bruit</h2>{quiet}<p>L’ablation complète de l’apprentissage part des gains nominaux (0,3 ; 1,2 ; 0,3) et b=0,08. La source n’alimente qu’une voie ; une cellule de la première couche ne reçoit donc qu’un port. Au gain central 1,2, la charge maximale sous le pulse canonique vaut environ 0,769 &lt; 1 : le réseau sans apprentissage ne s’amorce pas dans le contrôle sans bruit. Son échec n’est donc pas à lui seul une preuve que la coupure pendant la protection explique la robustesse au bruit.</p>
<h2>Protocole fixé avant la campagne</h2><p>Anneau de douze voies, trois parents par cellule depuis la couche précédente, 130 couches. Toutes les cellules sont initialement fraîches : q=0,1 ; gains (0,3 ; 1,2 ; 0,3) ; b=0,08 ; auxiliaires READY à leur repos. Les 128 pulses d’entraînement arrivent aux dates 8k. Les 24 pulses de test démarrent à 4096 et leurs intervalles suivent le motif 20 × (1 ; 1,1 ; 1,05 ; 1,2 ; 1 ; 1,15). Tous les événements d’entraînement sont propagés ; les gains appris ne sont jamais substitués à une histoire.</p>
<p>Chaque pulse de chaque connexion est multiplié par exp(0,1 Z − 0,005), Z gaussien standard : moyenne unitaire et coefficient de variation 10,025 %. La principale et son auxiliaire reçoivent cette même impulsion modifiée ; le seuil auxiliaire est recalculé. La gigue est uniforme et centrée, d’écart-type 0,03 ; un délai nominal de 0,1 maintient tous les délais positifs. Les vingt graines sont 0 à 19.</p>
<p>Les perturbations sont appariées par graine, couche, cellule, port et étiquette source (avec occurrence en cas de duplication). Une impulsion manquante ne décale pas les tirages suivants. Les labels ambigus utilisent leur ordinal ; l’appariement n’est alors plus une comparaison de la même cohorte identifiable. Ce champ aléatoire diffère des tirages séquentiels de la campagne précédente, tout en gardant les mêmes lois marginales. Les groupes avec bruit dès l’entraînement et seulement au test partagent les mêmes tirages de test pour les pulses identifiables correspondants.</p>
<h2>Définition exacte des interventions</h2><ul><li><b>Règle normale, bruit dès entraînement :</b> żᵢ = 8 vₑ,ᵢ seulement si la principale est READY ; b augmente par les marques seulement sous protection ; butées conservées. Bruit pendant les 128 pulses d’entraînement puis les 24 pulses de test.</li><li><b>Sans apprentissage :</b> żᵢ = 0 et ḃ = 0 dès t=0. Les gains restent nominaux et b=0,08. Toutes les autres dynamiques, phases et seuils sont conservés. Bruit dès l’entraînement.</li><li><b>Apprentissage autorisé sous protection :</b> seule la garde READY de żᵢ est retirée. Les gains peuvent augmenter pendant les phases rapide et lente, avec la même erreur différée et la même butée. La règle de b est conservée. Bruit dès l’entraînement.</li><li><b>Bruit seulement au test :</b> apprentissage normal sur les 128 pulses sans bruit ; bruit activé sur les pulses de test. Même délai nominal de 0,1.</li><li><b>Appris sous bruit puis figé :</b> règle normale et bruit pendant tout l’entraînement ; gains et b figés à t=4096, sans remise à zéro ni substitution de gains. Le bruit continue au test.</li></ul>
<p>Les formes des pulses émis restent canoniques ; le bruit est porté par les connexions. Les équations entre les événements et les seuils restent ceux du kit, hormis les interventions déclarées. La réserve énergétique E n’est pas intégrée, comme dans le simulateur fourni ; cette campagne ne constitue pas une validation énergétique indépendante.</p>
<h2>Mesures et incertitude</h2><p>La fraction retrouvée utilise toujours le dénominateur 12 × 24 = 288 à la couche 130. Une étiquette doit apparaître une fois sur une voie pour être retrouvée ; les pertes ne redéfinissent pas les voies de référence. Un mot complet sur le réseau exige exactement les 24 labels une fois sur chacune des douze voies, sans émission supplémentaire. Les événements ambigus et doublons figurent dans summary.csv. Les intervalles sont comparés au mot source effectif, pas à une période moyenne.</p>
<p>La graine est l’unité statistique ; les voies et pulses d’un même réseau ne sont pas traités comme des répétitions indépendantes. Les bandes des courbes sont les extrêmes observés sur vingt graines. Les intervalles exacts ci-dessous sont binomiaux (Clopper–Pearson) ; les intervalles bootstrap appariés et les différences entre conditions sont dans summary.json. Un bootstrap dégénéré à zéro pour vingt extinctions n’établit pas une probabilité universelle nulle.</p>{uncertainty}
<h2>Vérifications numériques</h2><p>VALIDATION.json conserve la régression sur 21 302 événements historiques (aucun écart de nombre ; erreur maximale de date &lt; 10⁻⁸), la comparaison locale avec le solveur précédent, et des tests analytiques des gardes : gain constant sous protection dans la règle normale, incrément complet de 0,6 sur le dépôt logarithmique sans cette garde, butée à 4, et gel effectif des gains et de b.</p><p>Le calcul ponctuel des racines utilise SciPy brentq, xtol=5×10⁻¹⁴, rtol=10⁻¹⁴. Les formules exponentielles sont identiques ; les sommes nulles sont évitées pour accélérer le calcul. kernel.diff décrit les changements par rapport au noyau ponctuel de la campagne précédente. Un rejeu complet à 130 couches de la graine 0 avec le solveur antérieur vérifie que la conclusion n’est pas créée par cette accélération ; son résultat de comparaison est dans REFERENCE_RECHECK.json.</p>
<h2>Détail par réalisation</h2>{indiv}<h2>Reproduction</h2><p>Python 3, NumPy, SciPy, Matplotlib. Depuis le dossier : <code>python build_kernel.py</code>, <code>python validate.py</code>, <code>python run.py --workers 8</code>, puis <code>python report.py</code>. Les résultats présents sont réutilisés ; déplacer output/ pour tout recalculer. La vérification de référence est disponible via <code>python reference_recheck.py</code>. Les sources de la campagne antérieure et le ZIP fourni sont conservés dans le dossier sources.</p><p>Statut : simulations ponctuelles exploratoires, sans certification, sans assertion générale de nécessité ou de suffisance de la règle locale.</p></html>'''
    (P/'rapport.html').write_text(body)
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.glob('*.py')}
    (P/'PROVENANCE.json').write_text(json.dumps({'python':platform.python_version(),'numpy':np.__version__,'protocol':{'depth':130,'width':12,'parents':3,'sigma_log_amplitude':.1,'jitter_standard_deviation':.03,'mean_edge_delay':.1,'training_pulses':128,'training_spacing':8,'test_pulses':24,'test_start':4096},'scripts_sha256':manifest,'source_kit_sha256':hashlib.sha256((P/'sources/A22_point_simulator_kit.zip').read_bytes()).hexdigest(),'seeds':list(range(20)),'status':'POINT_NOT_CERTIFIED'},indent=2))
    dest=P.parent.parent/'A22_ablations_130_20graines.zip';temp=dest.with_suffix('.tmp')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in P.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.log','.tmp'] and p.name!='interim.json':z.write(p,'A22_ablations/'+str(p.relative_to(P)))
    temp.replace(dest);print('ARCHIVE',dest,dest.stat().st_size)
if __name__=='__main__':report()
