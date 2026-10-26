A22 — robustesse ponctuelle

Ouvrir rapport.html pour le rapport et resultats.png pour les courbes.
summary.csv contient les métriques par essai ; output/*.json contient les émissions et états.

Reproduire depuis ce dossier :
python build_extension.py
python run_selected.py
python validate.py
python make_report.py

Python standard pour la campagne ; NumPy, SciPy et Matplotlib pour les vérifications et le rapport.
Pour recalculer tous les essais, déplacer output/ avant le lancement.

Les séries principales utilisent 6 graines et 24 impulsions de test après un entraînement complet de 128 impulsions.
Les résultats sont exploratoires et ponctuels. Le moteur certifié ne participe à aucun calcul.
Le source original fourni est conservé dans original_simulate.py et le kit voisin.
Les écarts avec ce source sont disponibles dans extension.diff.
