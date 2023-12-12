import yt_dlp as youtube_dl
import requests
import os
import random
import cv2
import json

# Dictionnaire pour convertir les codes pays en emoji de drapeaux
COUNTRY_FLAGS = {
    "us": "🇺🇸", "br": "🇧🇷", "fr": "🇫🇷", "jp": "🇯🇵", "de": "🇩🇪",
    "uk": "🇬🇧", "ca": "🇨🇦", "au": "🇦🇺", "it": "🇮🇹", "es": "🇪🇸",
    "ru": "🇷🇺", "cn": "🇨🇳", "in": "🇮🇳", "mx": "🇲🇽", "kr": "🇰🇷",
    "sa": "🇸🇦", "nl": "🇳🇱", "se": "🇸🇪", "no": "🇳🇴", "dk": "🇩🇰",
    "fi": "🇫🇮", "pl": "🇵🇱", "za": "🇿🇦", "ch": "🇨🇭", "at": "🇦🇹",
    "be": "🇧🇪", "ar": "🇦🇷", "cl": "🇨🇱", "co": "🇨🇴", "ve": "🇻🇪",
    "pe": "🇵🇪", "ua": "🇺🇦", "gr": "🇬🇷", "pt": "🇵🇹", "cz": "🇨🇿",
    "sk": "🇸🇰", "hu": "🇭🇺", "ro": "🇷🇴", "bg": "🇧🇬", "rs": "🇷🇸",
    "hr": "🇭🇷", "si": "🇸🇮", "lv": "🇱🇻", "ee": "🇪🇪", "lt": "🇱🇹",
    "ie": "🇮🇪", "nz": "🇳🇿", "my": "🇲🇾", "sg": "🇸🇬", "id": "🇮🇩",
    "ph": "🇵🇭", "th": "🇹🇭", "vn": "🇻🇳", "mm": "🇲🇲", "kh": "🇰🇭",
    "bd": "🇧🇩", "pk": "🇵🇰", "ae": "🇦🇪", "il": "🇮🇱", "eg": "🇪🇬",
    "ng": "🇳🇬", "ke": "🇰🇪", "gh": "🇬🇭", "dz": "🇩🇿", "ma": "🇲🇦",
    "tn": "🇹🇳", "tr": "🇹🇷", "ir": "🇮🇷", "iq": "🇮🇶", "sy": "🇸🇾",
    "lb": "🇱🇧", "jo": "🇯🇴", "qa": "🇶🇦", "kw": "🇰🇼", "om": "🇴🇲",
    "ye": "🇾🇪", "ge": "🇬🇪", "am": "🇦🇲", "az": "🇦🇿", "tm": "🇹🇲",
    "np": "🇳🇵", "lk": "🇱🇰", "bt": "🇧🇹", "mv": "🇲🇻", "bn": "🇧🇳",
    "tw": "🇹🇼", "hk": "🇭🇰", "mo": "🇲🇴", "kh": "🇰🇭", "la": "🇱🇦",
    "bd": "🇧🇩", "mm": "🇲🇲", "tl": "🇹🇱", "pg": "🇵🇬", "fj": "🇫🇯",
    "sb": "🇸🇧", "vu": "🇻🇺", "nc": "🇳🇨", "pf": "🇵🇫", "wf": "🇼🇫",
    "to": "🇹🇴", "tv": "🇹🇻", "ki": "🇰🇮", "nr": "🇳🇷", "ws": "🇼🇸",
    "as": "🇦🇸", "ck": "🇨🇰", "nu": "🇳🇺", "mp": "🇲🇵", "gu": "🇬🇺",
    "pw": "🇵🇼", "mh": "🇲🇭", "fm": "🇫🇲", "mh": "🇲🇭", "fm": "🇫🇲",
    "ki": "🇰🇮", "nr": "🇳🇷", "mh": "🇲🇭", "pw": "🇵🇼", "as": "🇦🇸",
    "ws": "🇼🇸", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿",
}

def get_flag_emoji(country_code):
    return COUNTRY_FLAGS.get(country_code.lower(), "")

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

def get_top_runs_with_video(game_id, game_name, used_runs_db):
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
                run_id = run['run']['id']
                if run_id in used_runs_db:
                    continue  # Ignorer les runs déjà utilisés
                video_link = run['run'].get('videos', {}).get('links', [{}])[0].get('uri', '')
                if video_link:
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
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'noplaylist': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        original_video_title = info_dict['title']
        video_extension = info_dict['ext']
        video_filename = f"{original_video_title}.{video_extension}"
        final_video_filename = f"{original_video_title}_finale.{video_extension}"
        final_video_path = os.path.join("A:\\Dossiers\\Documents\\SpeedRun_tiktok\\Video_final", final_video_filename)
        add_text_to_video(os.path.join(save_path, video_filename), final_video_path, run_info)
        print(f"Téléchargement et traitement de la vidéo '{original_video_title}' terminé.")

def add_text_to_video(video_path, final_video_path, run_info):
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(final_video_path, fourcc, cap.get(cv2.CAP_PROP_FPS), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
    country_flag = get_flag_emoji(run_info['country'])
    text_content = f"{run_info['player_name']} {country_flag}\n{run_info['game_name']}\n{run_info['category']}\n{run_info['date']}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        y0, dy = 50, 40  # Ajuster l'espacement vertical entre les lignes
        for i, line in enumerate(text_content.split('\n')):
            y = y0 + i*dy
            cv2.putText(frame, line, (50, y), font, 1, (255, 255, 255), 2)
        out.write(frame)
    cap.release()
    out.release()
    print(f"Montage vidéo terminé pour '{final_video_path}'.")

def main():
    games = get_games()
    if not games:
        print("Aucun jeu disponible.")
        return

    try:
        with open("used_runs_db.json", "r") as file:
            used_runs_db = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        used_runs_db = {}

    found_runs = 0
    while found_runs < 3:
        game_id, game_name = random.choice(list(games.items()))
        top_runs = get_top_runs_with_video(game_id, game_name, used_runs_db)
        if top_runs:
            for run in top_runs:
                if found_runs < 3:
                    video_url = run['video_url']
                    download_path = "A:\\Dossiers\\Documents\\SpeedRun_tiktok\\Video_download"
                    download_youtube_video(video_url, download_path, run)
                    print(f"Run sélectionné : {run}")
                    used_runs_db[run['run_id']] = run['category']
                    found_runs += 1
                else:
                    break
        else:
            print(f"Pas de runs du TOP 3 trouvés pour le jeu {game_name}")

    with open("used_runs_db.json", "w") as file:
        json.dump(used_runs_db, file)

if __name__ == "__main__":
    main()
