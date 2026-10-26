A22 — Coupure × plafond, restauration depuis un même état appris

Ouvrir rapport.html dans un navigateur. gains.png : figure de synthèse.
summary.json : groupes et IC bootstrap appariés exploratoires.
metrics.csv : métriques par graine, branche et bloc.
results/ : profils des 130 couches, incréments et demandes avant garde/plafond.
PROTOCOL.json : choix fixés après un pilote et avant la campagne principale.
VALIDATION.json : régression exacte contre le simulateur original et les archives.
AUDIT.json : recomptage indépendant de la demande et identité avant restauration.
INPUT_HASHES.json : empreintes des états initiaux fournis.

ATTENTION : campagne exploratoire du simulateur ponctuel fourni, sans moteur
certifié et sans intégration de la réserve E. Les 512 impulsions de continuation
sont séparées en blocs avec repos ; aucune stabilité permanente n'est déduite.
Les 20 graines, et non les voies ou les impulsions, sont les réplicats.
Le contrôle sans bruit est déterministe et n'a qu'une réalisation.
Le pilote graine 0/bruit moyen/sans garde/plafond 16 a précédé le protocole.

Reproduction : Python 3 + NumPy + Matplotlib, g++ C++17.
g++ -O3 -std=c++17 -ffp-contract=off src/experiment.cpp -o experiment
python validate.py
g++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC src/point_cell.cpp -o validation/instrumented.so
python local_check.py
python run.py
python analyze.py
python report.py
Les résultats terminés sont réutilisés ; déplacer results/ pour recalculer.
Le parallélisme de run.py est de huit processus ; il ne modifie pas les tirages.
Les états fournis (inputs/) sont des checkpoints normaux après 2048 pulses.
Les originaux des sources du noyau et de l'orchestrateur sont dans src/.
Aucun gain appris n'est modifié lors du chargement d'un checkpoint.
Le seul paramètre physique modifié est le plafond de gain ; la règle de b reste
celle du modèle initial. La restauration remet uniquement la garde READY.
