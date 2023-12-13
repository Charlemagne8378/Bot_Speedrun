import requests
import os
import random
import cv2
import json
import yt_dlp as youtube_dl
import re

# Constantes et configurations
API_BASE_URL = "https://www.speedrun.com/api/v1"
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
    "uz": "🇺🇿", "kz": "🇰🇿", "kg": "🇰🇬", "tj": "🇹🇯", "mn": "🇲🇳",
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
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
    "pf": "🇵🇫", "ki": "🇰🇮", "nc": "🇳🇨", "nu": "🇳🇺", "to": "🇹🇴",
    "wf": "🇼🇫", "sb": "🇸🇧", "vu": "🇻🇺", "fj": "🇫🇯", "pg": "🇵🇬",
    "tl": "🇹🇱", "nz": "🇳🇿", "au": "🇦🇺", "ck": "🇨🇰", "tv": "🇹🇻",
}
DOWNLOAD_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_download"
FINAL_VIDEO_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_final"
USED_RUNS_DB_FILE = "used_runs_db.json"

# Fonctions utilitaires
def get_flag_emoji(country_code):
    return COUNTRY_FLAGS.get(country_code.lower(), "")

def api_get(endpoint):
    response = requests.get(f"{API_BASE_URL}/{endpoint}")
    return response.json() if response.ok else None

# Fonctions principales
def get_games():
    response = api_get("games")
    return {game['id']: game['names']['international'] for game in response['data']} if response else {}

def get_player_info(player_id):
    response = api_get(f"users/{player_id}")
    if response and 'data' in response and response['data'] is not None:
        player = response['data']
        country_code = 'Inconnu'  # Valeur par défaut
        if 'location' in player and player['location'] is not None:
            country_code = player['location'].get('country', {}).get('code', 'Inconnu')
        return player['names']['international'], country_code
    return "Inconnu", "Inconnu"

def get_category_name(category_id):
    response = api_get(f"categories/{category_id}")
    return response['data']['name'] if response and 'data' in response else "Inconnue"

def get_top_run_from_category(game_id, category_id, game_name):
    response = api_get(f"leaderboards/{game_id}/category/{category_id}?top=1")
    if not response or 'runs' not in response['data'] or not response['data']['runs']:
        return None

    category_name = get_category_name(category_id)
    top_run_data = response['data']['runs'][0]['run']
    player_id = top_run_data['players'][0]['id']
    player_name, country_code = get_player_info(player_id)

    return {
        'game_name': game_name,
        'category_name': category_name,
        'player_name': player_name,
        'country': country_code,
        'date': top_run_data.get('date', 'Inconnue'),
        'video_url': top_run_data.get('videos', {}).get('links', [{}])[0].get('uri', '')
    }

def safe_filename(filename):
    """ Nettoie le nom de fichier en retirant ou remplaçant les caractères non autorisés. """
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)  # Remplacer par des caractères autorisés au besoin
    return filename

def download_and_process_video(video_url, run_info):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        'noplaylist': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_title = safe_filename(info_dict.get('title', 'downloaded_video'))
        video_extension = info_dict.get('ext', 'mp4')

    video_filename = f"{video_title}.{video_extension}"
    video_path = os.path.join(DOWNLOAD_PATH, video_filename)

    if not os.path.exists(video_path):
        # Essayer de trouver le fichier téléchargé en cherchant dans le dossier
        possible_files = [f for f in os.listdir(DOWNLOAD_PATH) if f.startswith(video_title) and f.endswith(video_extension)]
        if possible_files:
            video_path = os.path.join(DOWNLOAD_PATH, possible_files[0])
        else:
            print(f"Le fichier vidéo n'existe pas : {video_path}")
            return

    final_video_filename = os.path.join(FINAL_VIDEO_PATH, video_filename)
    add_text_to_video(video_path, final_video_filename, run_info)



def add_text_to_video(video_path, final_video_path, run_info):
    # Obtenir le drapeau du pays
    country_flag = get_flag_emoji(run_info['country'])

    # Construire le texte à ajouter à la vidéo
    text_content = f"{run_info['player_name']} {country_flag}\n{run_info['game_name']}\n{run_info['category_name']}\n{run_info['date']}"

    # Ouvrir la vidéo originale
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Erreur lors de l'ouverture de la vidéo : {video_path}")
        return

    # Récupérer les dimensions originales de la vidéo
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Définir les dimensions de sortie pour TikTok (9:16)
    output_height = 1920
    output_width = 1080

    # Calculer le facteur d'échelle et les nouvelles dimensions
    scale_factor = output_height / orig_height
    new_width = int(orig_width * scale_factor)
    x_margin = max((new_width - output_width) // 2, 0)

    # Utiliser le codec 'mp4v' pour la compatibilité avec le format MP4
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # Créer l'objet VideoWriter pour la sortie
    out = cv2.VideoWriter(final_video_path, fourcc, cap.get(cv2.CAP_PROP_FPS), (output_width, output_height))

    # Police de caractères pour le texte
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Traiter chaque frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Redimensionner et recadrer la frame
        resized_frame = cv2.resize(frame, (new_width, output_height))
        cropped_frame = resized_frame[:, x_margin:x_margin + output_width]

        # Ajouter le texte à la frame
        y0, dy = 50, 40
        for i, line in enumerate(text_content.split('\n')):
            y = y0 + i * dy
            cv2.putText(cropped_frame, line, (50, y), font, 1, (255, 255, 255), 2)

        # Écrire la frame modifiée dans le fichier de sortie
        out.write(cropped_frame)

    # Libérer les ressources
    cap.release()
    out.release()



def main():
    games = get_games()
    used_runs_db = json.load(open(USED_RUNS_DB_FILE, "r")) if os.path.exists(USED_RUNS_DB_FILE) else {}

    for _ in range(3):
        game_id, game_name = random.choice(list(games.items()))
        categories = api_get(f"games/{game_id}/categories")['data']
        for category in categories:
            if category['id'] not in used_runs_db.get(game_id, []):
                # Passer game_name en tant que troisième argument
                top_run = get_top_run_from_category(game_id, category['id'], game_name)
                if top_run and top_run['video_url']:
                    download_and_process_video(top_run['video_url'], top_run)
                    used_runs_db.setdefault(game_id, []).append(category['id'])
                    break

    json.dump(used_runs_db, open(USED_RUNS_DB_FILE, "w"))

if __name__ == "__main__":
    main()
