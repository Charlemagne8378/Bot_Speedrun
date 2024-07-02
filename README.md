# Script Speedrun

## Aperçu

Ce script réalise des vidéos en format verticale compatible Youtube Shorts, Tik Tok, Instragram etc à partir des URLs spécifiées dans `game_urls.txt` et en utilisant l'API de speedrun.com. Il effectue les tâches suivantes :

1. **Analyse des Données** : Extrait les informations pertinentes telles que les temps de run, les joueurs et les catégories à partir des données récupérées.
2. **Stockage des Données** : Enregistre les informations des runs dans `used_runs_db.json` pour éviter les doublons et garder une trace des runs déjà traités.
3. **Téléchargement des Vidéos** : Télécharge les vidéos des runs via une autre requête API dans le but de les utiliser pour le montage vidéo.

## Contenu du projet

- **Speedrun.py** : Script principal pour gérer et analyser les données de speedrun.
- **game_urls.txt** : Fichier texte contenant des URL de jeux pour le speedrunning.
- **used_runs_db.json** : Base de données JSON des runs déjà utilisés.
- **Drapeaux (dossier flags)** : Collection de drapeaux de pays au format SVG.
