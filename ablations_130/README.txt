A22 — ablations et apprentissage bruité à 130 couches

Ouvrir rapport.html ; les courbes sont dans resultats.png.
summary.csv : métriques par réalisation.
summary.json : moyennes, intervalles, comparaisons appariées.
by_layer.json : profils complets par couche.
output/ : émissions et états avant/après test.

Cinq conditions à vingt graines : normale avec bruit dès entraînement ; sans apprentissage ; apprentissage autorisé sous protection ; normale avec bruit seulement au test ; apprentissage bruité puis paramètres figés au test.
Bruit de charge : sigma logarithmique 0,10 ; gigue : écart-type 0,03 ; délai moyen 0,1.
128 impulsions d’entraînement, puis 24 impulsions irrégulières de test.

Reproduction : Python 3, NumPy, SciPy, Matplotlib.
python build_kernel.py
python validate.py
python run.py --workers 8
python reference_recheck.py
python report.py

Déplacer output/ pour tout recalculer. Les résultats existants sont réutilisés.
Statut : étude ponctuelle exploratoire, aucun moteur certifié.
