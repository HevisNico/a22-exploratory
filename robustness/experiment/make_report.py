import collections,html,json,hashlib,platform,zipfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import main
ROOT=Path(__file__).parent
def build():
    main()
    summary=json.loads((ROOT/'summary.json').read_text());rows=summary['runs'];by={r['name']:r for r in rows}
    def group(prefix):
        groups=collections.defaultdict(list)
        for r in rows:
            if r['name'].startswith(prefix):groups[r['name'].rsplit('_',1)[0]].append(r)
        return list(groups.items())
    def num(v,scale=1):return '—' if v is None else f'{v*scale:.4g}'
    def table(rs):
        out='<table><tr><th>Essai</th><th>Voies de référence</th><th>Mots complets / voies accessibles</th><th>Impulsions retrouvées</th><th>Erreur relative RMS des intervalles</th><th>Mots complets</th></tr>'
        for r in rs:out+=f"<tr><td>{html.escape(r['name'])}</td><td>{r['active_reference_lanes']}</td><td>{r.get('complete_word_lanes','—')} / {r.get('reachable_lanes','—')}</td><td>{num(r['recall'],100)} %</td><td>{num(r['relative_rms'],100)} %</td><td>{num(r['perfect_word_fraction'],100)} %</td></tr>"
        return out+'</table>'
    aggregated=[]
    for prefix in ['amp_','jitter_','q_','joint_','allnoise_']:
        for key,rs in group(prefix):
            aggregated.append({'name':key+f' (n={len(rs)})','active_reference_lanes':rs[0]['active_reference_lanes'],**{k:float(np.mean([r[k] for r in rs if r[k] is not None])) for k in ['recall','relative_rms','perfect_word_fraction']}})
    fig,axes=plt.subplots(2,3,figsize=(15,8.6));fig.patch.set_facecolor('#faf9f5')
    def curve(ax,prefix,key,field,label,color):
        groups=group(prefix);points=[]
        for name,rs in groups:
            vals=[r[field]*100 for r in rs if r[field] is not None]
            if vals:points.append((rs[0][key],np.mean(vals),min(vals),max(vals)))
        points.sort()
        if points:
            x,y,lo,hi=map(np.array,zip(*points));ax.plot(x,y,'o-',color=color,label=label);ax.fill_between(x,lo,hi,color=color,alpha=.15)
        ax.grid(alpha=.2)
    curve(axes[0,0],'amp_','sigma_amplitude','relative_rms','Intervalles appariés','#176b87');axes[0,0].set(title='Bruit des charges transportées',xlabel='σ logarithmique par connexion',ylabel='Erreur relative RMS (%)',xscale='log')
    curve(axes[0,1],'amp_','sigma_amplitude','recall','Impulsions retrouvées','#a0492b');axes[0,1].set(title='Pertes sous bruit de charge',xlabel='σ logarithmique par connexion',ylabel='Impulsions retrouvées (%)',xscale='log',ylim=(0,102))
    curve(axes[0,2],'jitter_','jitter','relative_rms','Gigue','#176b87');axes[0,2].set(title='Gigue des arrivées',xlabel='Écart-type (unité de temps)',ylabel='Erreur relative RMS (%)',xscale='log')
    gap=[r for r in rows if r['name'].startswith('gap_') and '_noisy_' not in r['name']]
    gap.sort(key=lambda r:r['gap']);axes[1,0].plot([r['gap'] for r in gap],[100*r['recall'] for r in gap],'o-',color='#a0492b');axes[1,0].set(title='Impulsions plus rapprochées',xlabel='Intervalle minimal à la source',ylabel='Impulsions retrouvées (%)',ylim=(0,102));axes[1,0].grid(alpha=.2)
    topolabels=['12 voies','24 voies','48 voies','5 parents','7 parents','5 parents +','7 parents +']
    topoprefix=['amp_0.03_','ring24_noisy_','ring48_noisy_','parents5_noisy_','parents7_noisy_','parents5_added_noisy_','parents7_added_noisy_']
    values=[]
    for prefix in topoprefix:
        rr=[r['recall']*100 for r in rows if r['name'].startswith(prefix) and r['recall'] is not None]
        values.append(float(np.mean(rr)) if rr else 0)
    axes[1,1].bar(range(len(values)),values,color='#176b87');axes[1,1].set_xticks(range(len(values)),topolabels,rotation=35,ha='right');axes[1,1].set(title='Topologies : bruit de charge σ=0,03',ylabel='Impulsions retrouvées (%)',ylim=(0,105))
    for depth,prefix,col in [(18,'amp_','#176b87'),(130,'depth130_amp_','#a0492b')]:
        curve(axes[1,2],prefix,'sigma_amplitude','recall',str(depth)+' couches',col)
    axes[1,2].set(title='Effet de la profondeur',xlabel='σ logarithmique par connexion',ylabel='Impulsions retrouvées (%)',xscale='log',ylim=(0,102));axes[1,2].legend()
    fig.suptitle('A22 — simulateur ponctuel fourni, entraînement complet puis 24 impulsions',fontsize=15)
    fig.text(.5,.006,'Traits : moyennes des répétitions. Bandes : min–max observés. Les erreurs de timing ne portent que sur les paires retrouvées.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.025,1,.96]);fig.savefig(ROOT/'resultats.png',dpi=170);plt.close(fig)
    unsupported=summary['unsupported']
    validation=json.loads((ROOT/'VALIDATION.json').read_text())
    body=f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>A22 — robustesse ponctuelle</title><style>body{{max-width:1100px;margin:40px auto;padding:0 25px;font:16px/1.55 system-ui;color:#172e39;background:#faf9f5}}h1,h2{{color:#13546c}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:20px 0}}th,td{{padding:8px;border-bottom:1px solid #ccd5d7;text-align:left}}th{{background:#e5eef0}}img{{width:100%}}code{{background:#e5eef0;padding:2px 5px}}.box{{border-left:4px solid #176b87;padding:12px 20px;background:white}}</style>
<h1>A22 — bruit, topologies et entrées</h1><p>Étude exploratoire du simulateur <code>simulate.py</code> fourni dans <code>A22_point_simulator_kit.zip</code>. Aucun moteur certifié importé. {len(rows)} simulations terminées dans le domaine du solveur ; {len(unsupported)} essais arrêtés par une garde explicite.</p>
<div class="box"><b>Lecture des résultats.</b> Les petits bruits perturbent progressivement les dates. Lorsque des franchissements de seuil changent, des impulsions peuvent disparaître : la fidélité du mot comporte alors des ruptures discrètes. Le taux moyen de pertes se mesure sur un nombre fini de graines ; aucun seuil universel n'est démontré.</div>
<img src="resultats.png" alt="Courbes de robustesse A22">
<h2>Constats principaux</h2><p>Après un entraînement sans bruit, à 18 couches, σ=0,01 sur les charges transportées donne 100 % des impulsions retrouvées et 0,118 % d’erreur relative RMS moyenne ; σ=0,03 donne 98,78 % et 0,522 % ; σ=0,10 donne 87,73 % et 1,401 %. Six graines par niveau. La gigue seule jusqu’à un écart-type de 0,05 conserve toutes les impulsions dans ces essais, avec environ 0,567 % d’erreur RMS.</p><p>À 130 couches, les deux réalisations à σ=0,01 conservent toutes les impulsions ; les deux réalisations à σ=0,10 n’en transmettent aucune à la sortie. La première couche sans émission de test est respectivement 103 et 100. Les pertes se propagent et s’aggravent avec la profondeur : il n’y a pas une rupture instantanée commune à tout le réseau.</p><p>Sans bruit, l’intervalle minimal 7 conserve les 24 impulsions dans toutes les voies de référence ; à 6, la fraction retrouvée est 80,90 %. Les formes alternant entre ±10 % de décroissance, à charge intégrale constante, conservent les impulsions et donnent environ 0,188 % d’erreur RMS. Les topologies testées sans bruit transmettent les mots complets dans leurs voies accessibles ; leur robustesse bruitée varie avec le graphe et la normalisation des gains.</p><h2>Protocole et sens des mesures</h2><p>Chaque essai repart des gains nominaux, q=0,1 et b=0,08 ; les 128 impulsions d'entraînement aux dates 8k sont entièrement simulées. Les mesures portent sur 24 impulsions supplémentaires à partir de 4096. Leurs intervalles répètent le motif 1, 1,1, 1,05, 1,2, 1, 1,15 multiplié par l'intervalle minimal indiqué. La source est uniquement la voie 0. Les paramètres auxiliaires restent nominaux par port. Aucun gain terminal n'est substitué à l'entraînement.</p>
<p><b>Impulsions retrouvées</b> : fraction des couples (voie active de référence, étiquette source) produisant une émission unique. La référence est la même topologie avec 24 impulsions espacées et sans bruit. <b>Mots complets</b> : fraction des voies de référence retrouvant les 24 étiquettes exactement une fois, sans émission supplémentaire ; cette mesure ne signifie pas que leurs dates sont exactes. <b>Erreur relative RMS</b> : racine de la moyenne des carrés de (intervalle de sortie − intervalle de source) / intervalle de source, uniquement pour deux étiquettes source consécutives retrouvées une fois. Elle doit être lue avec les pertes, car une erreur faible parmi les survivantes ne signifie pas une transmission fidèle. Mesures au dernier étage, sauf indication contraire.</p>
<p>Pour les courbes, les traits indiquent les moyennes entre graines, les bandes les extrêmes observés. Six graines pour les séries principales à 18 couches ; trois pour le bruit dès l'entraînement ; deux pour chaque topologie bruitée et chaque amplitude à 130 couches. Les résultats détaillés, dont les nombres de paires appariées et les émissions ambiguës, figurent dans <code>summary.csv</code>.</p>
<h2>Bruit</h2><p><b>Charges transportées</b> : chaque impulsion de chaque connexion est multipliée indépendamment par exp(σZ−σ²/2), Z gaussien standard. La moyenne de la charge est conservée ; son coefficient de variation vaut sqrt(exp(σ²)−1), proche de σ aux niveaux étudiés. Cette impulsion modifiée est reçue à la fois par la principale et son auxiliaire ; les dates de seuil auxiliaires sont recalculées à partir des équations.</p>
<p><b>Gigue</b> : variation uniforme, centrée, d'écart-type indiqué, indépendante par connexion et par impulsion. Un délai nominal de 0,1 est ajouté, suffisant pour garder tous les délais positifs (σ≤0,05). La référence de ces séries inclut ce même délai. <b>Charge interne q</b> : à chaque arrivée en mode prêt, saut uniforme centré d'écart-type 0,9σq ; projection à zéro si nécessaire. Il s'agit d'un protocole de perturbation impulsionnelle, pas d'un bruit blanc continu. Les autres équations restent celles du simulateur.</p>
<p>Le bruit affecte les impulsions de test dans les séries principales ; <code>allnoise</code> l'applique aussi pendant tout l'entraînement. Les séries <code>joint</code> combinent charges transportées et gigue.</p>
{table(aggregated)}
<p><b>Effet de la préparation.</b> Les séries où le bruit est présent pendant tout l’entraînement peuvent produire un état appris différent, plus robuste aux pulses testés. Les comparer aux séries où le bruit apparaît seulement après l’entraînement montre que la transition dépend aussi de l’histoire d’apprentissage ; ces petits échantillons ne prouvent pas un mécanisme général d’adaptation.</p><h2>Topologies</h2><p>Anneaux de 12, 24 et 48 voies ; voisinages à 3, 5 ou 7 parents. Dans la comparaison à gain total constant, le parent central garde un gain initial de 1,2 et les autres se partagent 0,6. Les variantes <code>added</code> donnent 0,3 à chaque parent latéral, donc augmentent le gain total : elles isolent le choix de normalisation. Les nombres de voies accessibles sont calculés par le graphe depuis la source ; ils distinguent absence de chemin et échec de transmission. La fraction retrouvée sans bruit est définie relativement aux voies de référence de ce même graphe ; elle ne mesure donc pas, à elle seule, la couverture spatiale. Les connexions aléatoires choisissent sans remise 3 ou 5 parents dans la couche précédente, indépendamment pour chaque cellule et étage ; trois graphes par degré. Toutes les connexions vont vers l'avant, entre couches consécutives. Aucun cycle dirigé ni saut de couche n'est testé. La variante bruitée utilise σ=0,03 sur les charges transportées.</p>
{table([r for r in rows if r['name'].startswith(('ring','parents','random'))])}
<h2>Entrées et profondeur</h2><p>Les intervalles minimaux testés sont 1,5, 2, 3, 4, 5, 6, 7, 8, 12 et 16. Le bruit éventuel reste à σ=0,03. Pour les formes d'impulsion, seuls les pulses de test de la source changent ; les émissions internes restent canoniques. La constante de décroissance est multipliée par 0,9, 0,95, 1,05 ou 1,1, fixe ou alternée. La durée varie séparément. La charge intégrale d'une impulsion source reste exactement 0,75 grâce à une renormalisation de l'amplitude. Une forme fixe peut déplacer la latence sans déformer les intervalles ; l'alternance teste une variation d'une impulsion à la suivante.</p>
{table([r for r in rows if r['name'].startswith(('gap_','shape_','width_','depth130'))])}
<h2>Vérifications et limites</h2><p>Le simulateur fourni retrouve les 21 302 événements historiques des 18 premières couches avec un écart maximal de 1,62×10⁻¹¹. Son extension retrouve les mêmes 21 302 événements avec un écart maximal de {validation['nominal']['max_date_error']:.3g}. Un contrôle indépendant par SciPy solve_ivp vérifie 27 premiers franchissements avec 3, 5 et 7 parents, trois décroissances et trois durées : écart maximal {validation['max_ODE_error']:.3g}. Ce contrôle local ne valide pas tous les chemins hybrides de la campagne.</p>
<p>Le fichier original est conservé ; <code>extension.diff</code> décrit les changements : nombre de ports variable, réponse analytique à chaque impulsion exponentielle modifiée, seuil auxiliaire recalculé, et perturbations explicites. La réserve E n'est pas intégrée, comme dans le kit. Les conclusions s'appliquent à ce simulateur ponctuel et à ces protocoles ; elles ne constituent ni une preuve pour toutes les réalisations, ni une certification du modèle à bruit continu ou à entrée arbitraire.</p>
<p>Un arrêt du solveur est rapporté séparément ; il n'est pas compté comme extinction physique. Le solveur exige la régénération de l'auxiliaire entre deux pulses d'un port et l'absence de chevauchement entre son courant brut et son erreur différée. Une forme trop longue peut violer cette dernière restriction.</p>
<pre>{html.escape(json.dumps(unsupported,indent=2))}</pre>
<h2>Reproduction</h2><p>Python 3 ; bibliothèque standard pour les simulations ; NumPy, SciPy et Matplotlib pour validation et rapport. Depuis le dossier extrait : <code>python build_extension.py</code>, <code>python run_selected.py</code>, <code>python validate.py</code>, <code>python make_report.py</code>. Les résultats existants sont réutilisés ; déplacer <code>output/</code> pour recalculer. Les fichiers JSON contiennent les graphes, émissions de test et états avant/après. Les événements historiques de référence sont inclus dans le dossier voisin <code>A22_point_simulator_kit</code>.</p></html>'''
    (ROOT/'rapport.html').write_text(body)
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')}
    (ROOT/'PROVENANCE.json').write_text(json.dumps({'python':platform.python_version(),'source_zip_sha256':hashlib.sha256((ROOT.parent.parent/'upload/A22_point_simulator_kit.zip').read_bytes()).hexdigest(),'scripts_sha256':manifest,'status':'EXPLORATORY_NOT_CERTIFIED'},indent=2))
    dest=ROOT.parent.parent/'A22_robustesse_resultats.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in ROOT.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.log'] and p.name not in ['interim.txt']:z.write(p,'A22_robustesse/experiment/'+str(p.relative_to(ROOT)))
        for p in (ROOT.parent/'A22_point_simulator_kit').rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,'A22_robustesse/A22_point_simulator_kit/'+str(p.relative_to(ROOT.parent/'A22_point_simulator_kit')))
    print('ARCHIVE',dest,dest.stat().st_size)
if __name__=='__main__':build()
