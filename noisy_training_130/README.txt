A22 — entraînement prolongé à 130 couches, vingt graines

Ouvrir rapport.html ; les courbes sont dans resultats.png.
summary.csv et summary.json : métriques et comparaisons appariées.
output_native/ : résultats principaux, contrôles à durée égale, checkpoints de toutes les tentatives.
PREPARATION_AUDIT.json : contrôle des 64 dernières impulsions d’entraînement dans les douze voies de sortie.

Politique fixée avant les tests : 512, 1024 puis 2048 impulsions si nécessaire, sans exclure de graine.
Bruit : sigma logarithmique des amplitudes 0,10 ; gigue uniforme d’écart-type 0,03 ; délai moyen 0,1.
Tests indépendants : 24 puis 128 impulsions irrégulières, chacun à partir d’une copie de l’état appris.
Les deux tests ne s’enchaînent pas. Pour chacun, comparaison adaptation active / gains et b figés.
Contrôle supplémentaire : entraînement sans bruit de même durée, puis mêmes perturbations au test.

Dépendances : Python 3, NumPy, SciPy, Matplotlib ; g++ C++17.
python build_kernel.py
python build_native.py
python native_run.py --workers 8
python control.py
python validate.py
python validate_native.py
python report.py

Les résultats présents sont réutilisés. Déplacer output_native/ pour recalculer.
La version Python de référence reste disponible via python run.py (plus lente).
Le pilote et les oracles Python ne sont pas comptés comme des graines indépendantes supplémentaires.
Aucun moteur certifié utilisé. Résultats ponctuels exploratoires.
