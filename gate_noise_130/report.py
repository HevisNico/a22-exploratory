"""Build a French report and exact static figures from completed seed-level results."""
import json, math, html
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
P=Path(__file__).resolve().parent
BLUE='#155e75';ORANGE='#c76b21';GRAY='#667085'
def pct(v,d=2):return f'{100*v:.{d}f}'.replace('.',',')+' %'
def ci(v):return '['+' ; '.join(f'{100*x:.2f}'.replace('.',',') for x in v)+'] points'
def figures(x):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
    fig,axs=plt.subplots(1,2,figsize=(11.4,4.3),layout='constrained')
    for c,col,offset,label in [('normal',BLUE,-.13,'Avec coupure'),('ungated',ORANGE,.13,'Sans coupure')]:
        groups=[x['groups'][f'{c}_L{l}_128_active'] for l in range(3)];y=np.array([g['mean_recall']*100 for g in groups]);limits=np.array([g['mean_recall_CI95'] for g in groups])*100
        axs[0].errorbar(np.arange(3)+offset,y,yerr=np.maximum(0,np.array([y-limits[:,0],limits[:,1]-y])),fmt='o',capsize=4,color=col,label=label)
        axs[1].bar(np.arange(3)+offset*1.4,[g['full_words'] for g in groups],width=.32,color=col,label=label)
    axs[0].set(ylabel='Étiquettes retrouvées exactement une fois (%)',ylim=(-3,103),title='Transmission à la couche 130')
    axs[1].set(ylabel='Réseaux avec mot intégral sur 12 voies',ylim=(0,21),yticks=[0,5,10,15,20],title='128 impulsions indépendantes')
    for ax in axs:ax.set_xticks(range(3),['Faible\nσ = 0,05','Moyen\nσ = 0,10','Fort\nσ = 0,15']);ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
    axs[0].legend(frameon=False,loc='lower left');fig.savefig(P/'resultats.png',dpi=200);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11.4,4.2),layout='constrained')
    for c,col,mark,label in [('normal',BLUE,'o','Avec coupure'),('ungated',ORANGE,'s','Sans coupure')]:
        yy=[x['training'][f'{c}_L{l}']['mean_gain'] for l in range(3)];zz=[x['training'][f'{c}_L{l}']['gain_cap_fraction']*100 for l in range(3)]
        axs[0].plot(range(3),yy,marker=mark,color=col,label=label);axs[1].plot(range(3),zz,marker=mark,color=col,label=label)
    axs[0].set(ylabel='Gain moyen (tous les ports et cellules)',ylim=(0,4.15),title='État appris après 2 048 impulsions');axs[1].set(ylabel='Ports à la butée de gain 4 (%)',ylim=(-3,103),title='Stabilisation ou saturation ?')
    for ax in axs:ax.set_xticks(range(3),['Faible','Moyen','Fort']);ax.grid(axis='y',alpha=.16)
    axs[0].legend(frameon=False);fig.savefig(P/'mecanisme.png',dpi=200);plt.close(fig)
def build():
    x=json.loads((P/'summary.json').read_text());figures(x)
    out=P/'rapport_A22_coupure_bruit.pdf'
    fontroot=Path('/usr/share/fonts/truetype/dejavu')
    for name,file in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fontroot/file)))
    pdfmetrics.registerFontFamily('D',normal='D',bold='DB',italic='D',boldItalic='DB')
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyFR',fontName='D',fontSize=9,leading=13,textColor=colors.HexColor('#253345'),spaceAfter=8));styles.add(ParagraphStyle(name='TitleFR',fontName='DB',fontSize=23,leading=29,textColor=colors.HexColor(BLUE),spaceAfter=13));styles.add(ParagraphStyle(name='HFR',fontName='DB',fontSize=14,leading=19,textColor=colors.HexColor(BLUE),spaceBefore=8,spaceAfter=9));styles.add(ParagraphStyle(name='SmallFR',fontName='D',fontSize=7.3,leading=10,textColor=colors.HexColor(GRAY),spaceAfter=6))
    story=[]
    def p(s,style='BodyFR'):story.append(Paragraph(s,styles[style]))
    def table(data,widths):
        body=[[Paragraph(str(v),styles['SmallFR']) for v in row] for row in data];t=Table(body,colWidths=widths,hAlign='LEFT',repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8f1f4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#9db7c0')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#dde4e9')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t);story.append(Spacer(1,10))
    primary=[x['paired'][f'L{l}_normal_minus_ungated_128_active'] for l in range(3)]
    supported=[a['mean_delta']>0 and a['CI95'][0]>0 and a['sign_p_Holm_3']<.05 for a in primary]
    if all(supported):verdict='La coupure améliore la transmission aux trois niveaux de bruit testés.'
    elif any(supported):verdict='Le bénéfice de la coupure dépend du niveau de bruit ; la nécessité générale n’est pas établie.'
    else:verdict='Cette campagne ne démontre pas que la coupure est nécessaire à la transmission profonde.'
    p('A22 / EXPÉRIENCE DE CAUSALITÉ', 'SmallFR');p('Coupure locale<br/>et adaptation au bruit','TitleFR');p('130 couches · 12 voies · 20 graines appariées · 3 niveaux de bruit','HFR');p('<b>'+verdict+'</b>')
    p('L’apprentissage sous bruit apporte un bénéfice net face à l’apprentissage propre, même lorsque les paramètres sont figés au test. La coupure limite fortement la saturation des gains ; sa nécessité pour la transmission n’est pas établie.')
    p('Le seul changement de l’ablation autorise l’augmentation des gains lorsque la cellule principale est protégée. La règle de récupération b, les erreurs différées, les seuils, la topologie et les butées restent identiques. Chaque apprentissage part du même état nominal et reçoit 2 048 impulsions, sans sélection des graines.')
    story.append(Image(str(P/'resultats.png'),width=490,height=185))
    data=[['Bruit (σ ; gigue)','Avec coupure : rappel / mots','Sans coupure : rappel / mots','Différence appariée ; IC 95 %']]
    for l in range(3):
        a=x['groups'][f'normal_L{l}_128_active'];b=x['groups'][f'ungated_L{l}_128_active'];d=primary[l]
        data.append([f'{.05*(l+1):.2f} ; {.015*(l+1):.3f}',f'{pct(a["mean_recall"])} / {a["full_words"]}/20',f'{pct(b["mean_recall"])} / {b["full_words"]}/20',f'{100*d["mean_delta"]:+.2f} points<br/>{ci(d["CI95"])}'])
    table(data,[89,129,129,143])
    p('Critère principal : 128 impulsions de test indépendantes, adaptation active, sortie à la couche 130. Rappel = proportion des couples voie-étiquette présents exactement une fois ; les doublons ne sont pas des réussites. Mot intégral = 128 étiquettes ordonnées sur chacune des 12 voies, sans événement supplémentaire. IC de la différence exprimé en points de pourcentage.','SmallFR')
    story.append(PageBreak())
    p('Ce que le réseau a appris','TitleFR')
    p('Le contrôle appris sans bruit utilise exactement 2 048 impulsions, puis reçoit les mêmes perturbations de test que les conditions bruitées. Un second test fige les gains et b au début de l’évaluation ; les états appris sont copiés et les tests ne s’enchaînent pas.')
    data=[['Niveau','Appris sous bruit ; actif','Appris sans bruit ; actif','Appris sous bruit ; figé','Appris sans bruit ; figé','Différence bruité - propre, figés ; IC']]
    for l in range(3):
        a=x['groups'][f'normal_L{l}_128_active'];b=x['groups'][f'clean_L{l}_128_active'];c=x['groups'][f'normal_L{l}_128_frozen'];e=x['groups'][f'clean_L{l}_128_frozen'];d=x['paired'][f'L{l}_normal_minus_clean_128_frozen']
        data.append([['Faible','Moyen','Fort'][l],f'{pct(a["mean_recall"])}<br/>{a["full_words"]}/20 mots',f'{pct(b["mean_recall"])}<br/>{b["full_words"]}/20 mots',f'{pct(c["mean_recall"])}<br/>{c["full_words"]}/20 mots',f'{pct(e["mean_recall"])}<br/>{e["full_words"]}/20 mots',f'{100*d["mean_delta"]:+.2f} points<br/>{ci(d["CI95"])}'])
    table(data,[46,88,88,88,88,92])
    p('Transfert entre niveaux de bruit','HFR');p('Rappel moyen au test de 128 impulsions, gains et b figés. L’évaluation utilise le même champ aléatoire standardisé, mis à l’échelle au niveau de bruit indiqué.')
    data=[['Apprentissage / test','Faible','Moyen','Fort']]
    for a in range(3):data.append([['Faible','Moyen','Fort'][a]]+[pct(x['frozen_transfer128'][f'train{a}_test{b}']['mean_recall']) for b in range(3)])
    table(data,[160,110,110,110])
    p('Précision temporelle parmi les paires retrouvées','HFR')
    data=[['Bruit de test','RMS relative avec coupure','RMS relative sans coupure']]
    for l in range(3):
        aa=x['groups'][f'normal_L{l}_128_active'];bb=x['groups'][f'ungated_L{l}_128_active']
        data.append([['Faible','Moyen','Fort'][l],pct(aa['mean_relative_rms'],3) if aa['mean_relative_rms'] is not None else 'Non mesurable',pct(bb['mean_relative_rms'],3) if bb['mean_relative_rms'] is not None else 'Non mesurable'])
    table(data,[120,185,185])
    p('Une amélioration par rapport à l’apprentissage propre établit un bénéfice de l’exposition au bruit dans ce protocole. Elle ne prouve pas, à elle seule, une spécialisation optimale à son niveau exact. La matrice de transfert permet de vérifier si un apprentissage plus bruité bénéficie aussi aux tests plus calmes.')
    p('Les tests courts de 24 impulsions sont conservés dans summary.json et summary.csv. Ils constituent une vérification secondaire ; ils ne remplacent pas le critère principal de 128 impulsions. Les étiquettes ambiguës, doublons, erreurs d’ordre et erreurs temporelles sont comptés séparément. Une faible erreur temporelle parmi les paires survivantes ne compense pas les pertes.','SmallFR')
    story.append(PageBreak())
    p('Coupure et arrêt des mises à jour','TitleFR')
    story.append(Image(str(P/'mecanisme.png'),width=490,height=181))
    data=[['Condition','Niveau','Réseaux prêts*','Gain moyen','Ports en butée','Δz tardif / Δb tardif**']]
    for c,label in [('normal','Avec coupure'),('ungated','Sans coupure')]:
        for l in range(3):
            t=x['training'][f'{c}_L{l}'];data.append([label,['Faible','Moyen','Fort'][l],f'{t["prepared_tail128"]}/20',f'{t["mean_gain"]:.3f}',pct(t['gain_cap_fraction'],1),f'{t["tail128_delta_z"]:.3g} / {t["tail128_delta_b"]:.3g}'])
    table(data,[83,53,65,64,80,145])
    p('* Les 128 dernières impulsions d’entraînement sont transmises intégralement, dans l’ordre, sur les 12 voies de la couche 130. Ce critère est rapporté après calcul et ne filtre aucun essai.<br/>** Sommes des incréments sur toutes les cellules et tous les ports associés aux 128 dernières étiquettes d’entraînement ; moyenne entre les 20 graines. Δz est mesuré en logarithme de gain.','SmallFR')
    late=sum(x['training'][f'normal_L{l}']['tail128_gain_moves'] for l in range(3))
    if late>0:p('<b>L’arrêt global de l’apprentissage n’est pas établi :</b> des gains augmentent encore sur la fenêtre finale dans la condition normale. La coupure constitue une garde locale de l’apprentissage ; cela ne signifie pas que tous les paramètres d’un réseau soumis durablement au bruit cessent définitivement d’évoluer.')
    else:p('Aucune augmentation de gain n’est observée dans la fenêtre finale pour la condition normale. Il s’agit d’une observation finie, à compléter par les incréments de b et les fractions en butée ; elle ne démontre pas un arrêt permanent sous bruit.')
    p('Le bruit d’amplitude est lognormal, donc non borné. Même un régime stable sur cette séquence finie ne donne pas de garantie pour toute perturbation future. La saturation des gains à 4 est un mécanisme d’arrêt distinct d’une extinction de l’erreur grâce à la coupure.')
    story.append(PageBreak())
    p('Protocole et audit','TitleFR')
    p('<b>Milieu simulé.</b> Réseau en anneau, 12 voies par couche, parents j-1, j, j+1 ; seule la voie 0 reçoit la source. Gains initiaux (0,3 ; 1,2 ; 0,3), b = 0,08. Entraînement : 2 048 impulsions espacées de 8 unités. Tests : 24 ou 128 impulsions, intervalles irréguliers de 20 à 24 unités, après le même silence source que dans les essais fournis.')
    p('<b>Bruit.</b> À chaque transmission et sur chaque port : amplitude exp(σZ - σ²/2), Z normal standard ; gigue uniforme centrée d’écart-type 0,015, 0,030 ou 0,045, associée respectivement à σ = 0,05, 0,10 ou 0,15 ; délai nominal 0,1. La gigue maximale au niveau fort reste inférieure au délai. Aucun autre type de bruit n’est ajouté.')
    p('<b>Appariement et indépendance.</b> Champ déterministe SplitMix64 avec transformation de Box-Muller, indexé par graine, couche, voie, port, phase, étiquette et occurrence. Les phases aléatoires 0, 24 et 128 séparent apprentissage et tests. Le même bruit standardisé sert aux conditions comparées. Les graines 0 à 19 sont de nouvelles réalisations, pas une reprise à l’identique des champs aléatoires précédents. Le contrôle appris sans bruit a un état d’entraînement déterministe commun, évalué sous 20 champs de bruit de test.')
    p('<b>Statistiques.</b> Unité de réplication : la graine, jamais une voie ou une impulsion. IC bootstrap apparié à 95 %, 20 000 rééchantillonnages. Tests des signes bilatéraux ; correction de Holm pour les trois comparaisons principales de coupure. Les autres comparaisons restent exploratoires. Un résultat de 20/20 mots complets correspond à un IC binomial exact de [83,16 % ; 100 %], pas à une probabilité garantie de 100 %.')
    vals=[f'{["faible","moyen","fort"][l]} : p = {primary[l]["sign_p_two_sided"]:.4g}, Holm = {primary[l]["sign_p_Holm_3"]:.4g}' for l in range(3)]
    p('<b>Tests principaux.</b> '+' ; '.join(vals)+'.')
    p('<b>Validation numérique.</b> Les 12 contrôles locaux passent pour les deux règles, avec et sans gel. Le réseau normal à 130 couches et 512 impulsions concorde avec le solveur Python : écart maximal de logarithme de gain 1,50 × 10<super>-6</super> ; le contrôle sans coupure à 128 impulsions passe aussi. Dans l’audit de racines à 2 048 impulsions, les scores discrets et étiquettes de sortie sont identiques, mais le seuil absolu de 10<super>-5</super> sur les états échoue : écart maximal de temps d’état 5,43 × 10<super>-4</super>, de b 5,12 × 10<super>-4</super>. L’écart de RMS relative au test reste inférieur à 1,13 × 10<super>-8</super>. Les essais initiaux sont recalculés avec le solveur final ; les audits sont conservés. Il s’agit d’un simulateur ponctuel, sans moteur certifié ni preuve par intervalles.')
    p('<b>Correction par rapport au test court antérieur.</b> Son générateur réutilisait, pour certains pulses de test, des clés d’apprentissage à partir de l’étiquette 128. La présente campagne emploie des clés séparées pour toutes les évaluations ; ses résultats doivent donc être lus comme une nouvelle expérience.')
    p('<b>Reproduire.</b> Depuis le dossier de l’archive : python build.py ; python run_campaign.py --workers 8 ; python analyze.py ; python report.py. Déplacer output/ pour recalculer. Le protocole fixé avant les nouveaux résultats est dans PROTOCOL.json ; les entrées, sources et sorties sont identifiées par SHA-256 dans PROVENANCE.json. Les contrôles et pilotes ne comptent pas comme graines supplémentaires.','SmallFR')
    def footer(canvas,doc):
        canvas.setFont('D',7);canvas.setFillColor(colors.HexColor(GRAY));canvas.drawString(45,27,'A22 · Campagne coupure × bruit · Étude numérique exploratoire');canvas.drawRightString(550,27,str(doc.page))
    doc=SimpleDocTemplate(str(out),pagesize=(595.28,841.89),rightMargin=45,leftMargin=45,topMargin=40,bottomMargin=42,title='A22 - Coupure locale et adaptation au bruit',author='Analyse expérimentale')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(out)
if __name__=='__main__':build()
