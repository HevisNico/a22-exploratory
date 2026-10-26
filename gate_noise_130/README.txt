A22 - Ablation de la coupure et trois niveaux de bruit

Ouvrir rapport_A22_coupure_bruit.pdf pour la synthèse française.
resultats.png : transmission et mots intégraux à 130 couches.
mecanisme.png : gains appris et saturation.

Protocole : 130 couches, 12 voies, 20 graines appariées par niveau.
Bruit amplitude sigma = 0.05 / 0.10 / 0.15 ; gigue écart-type = 0.015 / 0.030 / 0.045.
2 048 impulsions d'apprentissage dans toutes les conditions, sans sélection des graines.
Règle normale contre suppression de la seule garde READY de l'augmentation des gains.
Contrôles : apprentissage propre de même durée, gel de gains et b, transfert entre niveaux.
Tests 24 et 128 impulsions indépendants de l'apprentissage et l'un de l'autre.

Fichiers :
PROTOCOL.json : protocole fixé avant les nouveaux résultats.
summary.json : groupes, IC et comparaisons appariées ; critère principal 128 actif.
summary.csv : tous les résultats à la couche 130.
training.csv : préparation, gains, butées, mises à jour tardives par graine.
profiles.csv : profils de transmission par couche.
output/ : résultats bruts et états appris ; clean_training.* est le contrôle déterministe commun.
AUDIT.json : intégrité des états, gel exact, recomptage indépendant des sorties finales.
VALIDATION.json et validation/ : solveur Python, contrôle de racines et sensibilité numérique.
PROVENANCE.json : empreintes SHA-256 des entrées, sources et sorties.
ENVIRONMENT.json et requirements.txt : environnement du calcul.

Reproduire depuis ce dossier :
python build.py
python run_campaign.py --workers 8
python audit.py
python analyze.py
python report.py
Les résultats complets sont réutilisés. Pour recalculer, déplacer output/.
Pour les contrôles du solveur : python validate.py ; python validate.py --full.
La reconstruction nécessite g++ C++17 et les dépendances Python listées.

Lecture : l'unité statistique est la graine. Les 12 voies et les impulsions d'une même
réalisation ne sont pas des réplicats indépendants. Le rappel exige une occurrence
exacte ; le mot intégral exige aussi l'ordre et l'absence d'événements supplémentaires.
Les analyses secondaires restent exploratoires. Un arrêt observé pendant 128 impulsions
ne prouve pas une auto-terminaison permanente sous bruit lognormal non borné.

Le générateur aléatoire est nouveau ; les graines numériques ne reproduisent pas les
champs de bruit des archives antérieures. Il n'y a aucun moteur certifié dans ce calcul.
Les premiers essais au solveur de racines par bissection ont été recalculés avec le
solveur final. L'audit long conserve le constat d'une sensibilité des états continus,
sans différence des scores discrets dans le cas comparé.
