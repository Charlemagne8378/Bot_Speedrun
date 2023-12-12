import yt_dlp as youtube_dl
import requests
import os
import random
import cv2

def get_games():
    url = "https://www.speedrun.com/api/v1/games"
    response = requests.get(url)
    if response.status_code == 200:
        games = response.json()['data']
        return {game['id']: game['names']['international'] for game in games}
    else:
        print(f"Erreur lors de la récupération des jeux. Statut {response.status_code}")
        return {}

def get_player_info(player_reference):
    player_id = player_reference.get('id') or player_reference['uri'].split('/')[-1]
    url = f"https://www.speedrun.com/api/v1/users/{player_id}"
    response = requests.get(url)
    if response.status_code == 200:
        player_data = response.json().get('data')
        if player_data:
            player_name = player_data['names']['international']
            country_code = player_data.get('location', {}).get('country', {}).get('code', 'Inconnu') if player_data.get('location') else 'Inconnu'
            return player_name, country_code
        else:
            return "Inconnu", "Inconnu"
    else:
        return "Inconnu", "Inconnu"

def get_top_runs_with_video(game_id, game_name):
    categories_url = f"https://www.speedrun.com/api/v1/games/{game_id}/categories"
    categories_response = requests.get(categories_url)
    if categories_response.status_code != 200:
        print(f"Erreur lors de la récupération des catégories pour le jeu {game_id}. Statut {categories_response.status_code}")
        return []

    categories = categories_response.json()['data']
    top_runs = []
    for category in categories:
        category_id = category['id']
        leaderboard_url = f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category_id}?top=3"
        leaderboard_response = requests.get(leaderboard_url)
        if leaderboard_response.status_code == 200:
            leaderboard = leaderboard_response.json()['data']
            runs = leaderboard['runs']
            for run in runs:
                video_link = run['run'].get('videos', {}).get('links', [{}])[0].get('uri', '')
                if video_link:
                    run_id = run['run']['id']
                    player_info = run['run']['players'][0]
                    player_name, country = get_player_info(player_info)
                    category_name = category['name']
                    run_date = run['run'].get('date', 'Date inconnue')
                    top_runs.append({
                        'game_name': game_name,
                        'run_id': run_id,
                        'player_name': player_name,
                        'country': country,
                        'category': category_name,
                        'date': run_date,
                        'video_url': video_link
                    })
    return top_runs

def download_youtube_video(url, save_path, run_info):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(save_path, '%(id)s.%(ext)s'),
        'noplaylist': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_filename = ydl.prepare_filename(info_dict)
        final_video_path = os.path.join(save_path, "video_finale.mp4")
        add_text_to_video(video_filename, final_video_path, run_info)

def add_text_to_video(video_path, final_video_path, run_info):
    cap = cv2.VideoCapture(video_path)

    # Définir le codec et créer un objet VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(final_video_path, fourcc, cap.get(cv2.CAP_PROP_FPS), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

    # Préparer le texte à ajouter
    text_content = f"{run_info['player_name']}\n{run_info['country']}\n{run_info['game_name']}\n{run_info['category']}\n{run_info['date']}\n{run_info['video_url']}"
    font = cv2.FONT_HERSHEY_SIMPLEX

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Ajouter du texte à la frame
        y0, dy = 50, 30
        for i, line in enumerate(text_content.split('\n')):
            y = y0 + i*dy
            cv2.putText(frame, line, (50, y), font, 1, (255, 255, 255), 2)

        out.write(frame)

    cap.release()
    out.release()

def main():
    games = get_games()
    if not games:
        print("Aucun jeu disponible.")
        return

    found_runs = 0
    while found_runs < 3:
        game_id, game_name = random.choice(list(games.items()))
        top_runs = get_top_runs_with_video(game_id, game_name)
        if top_runs:
            for run in top_runs:
                if found_runs < 3:
                    video_url = run['video_url']
                    download_path = "A:\\Dossiers\\Documents\\SpeedRun_tiktok\\Video_download"
                    download_youtube_video(video_url, download_path, run)
                    print(f"Run sélectionné : {run}")
                    found_runs += 1
                else:
                    break
        else:
            print(f"Pas de runs du TOP 3 trouvés pour le jeu {game_name}")

if __name__ == "__main__":
    main()
