import os
import random
import re
import json
import datetime
import requests
import yt_dlp as youtube_dl
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cairosvg
from io import BytesIO
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import google.oauth2.credentials
from urllib.parse import urlparse, parse_qs

# Variables + Constantes

API_BASE_URL = "https://www.speedrun.com/api/v1"
COUNTRY_FLAGS_FILE = "country_flags.json"
TOKEN_FILE = "token.json"
SCHEDULED_DATES_FILE = "scheduled_dates.json"
USED_RUNS_DB_FILE = "used_runs_db.json"
client_secrets_file = "client_secrets.json"
DOWNLOAD_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_download"
FINAL_VIDEO_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_final"
FLAGS_FOLDER_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\flags"
FONT_PATH = "arial.ttf"
scopes = ["https://www.googleapis.com/auth/youtube.upload"]
api_cache = {}

def api_get(endpoint):
    global api_cache
    if endpoint in api_cache:
        return api_cache[endpoint]

    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        if response.status_code == 200:
            api_cache[endpoint] = response.json()
            return api_cache[endpoint]
    except requests.RequestException as e:
        print(f"Error in API request: {e}")
    return None

def get_video_id_from_url(video_url):
    parsed_url = urlparse(video_url)
    if "youtube" in parsed_url.netloc:
        return parse_qs(parsed_url.query)['v'][0]
    # Ajouter d'autres logiques pour différents formats d'URL si nécessaire.
    return None

def update_used_runs_db(game_id, category_id, video_id):
    if os.path.exists(USED_RUNS_DB_FILE):
        with open(USED_RUNS_DB_FILE, "r") as file:
            used_runs_db = json.load(file)
    else:
        used_runs_db = {}

    used_runs_db.setdefault(game_id, {}).setdefault(category_id, []).append(video_id)

    with open(USED_RUNS_DB_FILE, "w") as file:
        json.dump(used_runs_db, file, indent=4)

def update_scheduled_dates(post_time):
    if os.path.exists(SCHEDULED_DATES_FILE):
        with open(SCHEDULED_DATES_FILE, "r") as file:
            scheduled_dates = json.load(file)
    else:
        scheduled_dates = {}

    str_date = post_time.strftime("%d/%m/%Y")
    str_time = post_time.strftime("%H:%M:%S")
    scheduled_dates.setdefault(str_date, []).append(str_time)

    with open(SCHEDULED_DATES_FILE, "w") as file:
        json.dump(scheduled_dates, file, indent=4)

def process_video(video_path, run_info, country_flags):
    country_flag_path = get_flag_image_path(run_info['country'], country_flags)
    text_content = f"{run_info['player_name']}\n{run_info['game_name'].strip()}\n{run_info['category_name']}\n{run_info['date']}"

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video: {video_path}")
        return None

    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    new_width = 720
    new_height = int((9 / 16) * new_width)

    vert_padding = int((1280 - new_height) / 2)
    horiz_padding = int((720 - new_width) / 2)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    final_video_name = f"{run_info['game_name']} - {run_info['category_name']} - {run_info['player_name']}.mp4"
    final_video_path = os.path.join(FINAL_VIDEO_PATH, safe_filename(final_video_name))

    out = cv2.VideoWriter(final_video_path, fourcc, cap.get(cv2.CAP_PROP_FPS), (720, 1280))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (new_width, new_height))

        letterbox_frame = np.zeros((1280, 720, 3), dtype=np.uint8)
        letterbox_frame[vert_padding:vert_padding + new_height, horiz_padding:horiz_padding + new_width] = frame

        frame_pil = Image.fromarray(cv2.cvtColor(letterbox_frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(frame_pil)
        font = ImageFont.truetype(FONT_PATH, 32)
        x, y = 50 + horiz_padding, 50

        draw.text((x, y), text_content, font=font, fill="white")

        text_x, text_y, text_width, text_height = draw.textbbox((x, y), run_info['player_name'], font=font)
        flag_x = text_x + text_width

        if country_flag_path and country_flag_path.endswith('.svg'):
            png_image = cairosvg.svg2png(url=country_flag_path)
            flag_image = Image.open(BytesIO(png_image)).resize((50, 30))
            frame_pil.paste(flag_image, (flag_x, y), flag_image)

        letterbox_frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
        out.write(letterbox_frame)

    cap.release()
    out.release()

    return final_video_path

def create_youtube_client(client_secrets_file, scopes):
    credentials = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as file:
            token_data = json.load(file)
            credentials = google.oauth2.credentials.Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=scopes
            )

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes)
            credentials = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(credentials.to_json())

    return googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)


def upload_video(file_name, run_info):
    title = f"{run_info['player_name']} - {run_info['game_name']} - {run_info['category_name']} #Shorts"
    description = (
        "TikTok : https://www.tiktok.com/@speedrunspectre\n"
        "Instagram : https://www.instagram.com/speedrunspectre/\n\n"
        f"SpeedRun Link : {run_info['run_link']}\n"
        f"SpeedRun Profile : {run_info['player_profile_link']}\n"
    )
    tags = ["speedrun", "gameplay", run_info['game_name']]  # Définir les tags ici

    # Désactiver la vérification HTTPS pour l'exécution locale.
    # NE PAS laisser cette option activée en production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Nom et version du service API.
    api_service_name = "youtube"
    api_version = "v3"

    # Le fichier client_secrets.json doit être dans le même dossier que le script.
    client_secrets_file = "client_secrets.json"

    # Récupérer les informations d'identification et créer un client API.
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    # Utiliser run_local_server si run_console n'est pas disponible.
    credentials = flow.run_local_server(port=0)
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    # Créer la requête d'upload.
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "20",  # Changer si une autre catégorie est préférée.
                "description": description,
                "title": title,
                "tags": tags
            },
            "status": {
                "privacyStatus": "unlisted"  # Changer si une autre confidentialité est préférée.
            }
        },
        
        media_body=googleapiclient.http.MediaFileUpload(file_name, resumable=True)
    )
    
    response = request.execute()

    print(response)

def process_and_upload_video(video_path, run_info, country_flags):
    final_video_path = process_video(video_path, run_info, country_flags)
    if final_video_path:
        upload_video(final_video_path, run_info)


def read_scheduled_dates():
    if os.path.exists(SCHEDULED_DATES_FILE):
        with open(SCHEDULED_DATES_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                # Le fichier est vide ou mal formé, retourner une structure de base
                return {}
    else:
        # Le fichier n'existe pas, retourner une structure de base
        return {}

def write_scheduled_dates(scheduled_dates):
    with open(SCHEDULED_DATES_FILE, "w") as file:
        json.dump(scheduled_dates, file, indent=4)


def get_next_available_slot():
    scheduled_dates = read_scheduled_dates()
    current_date = datetime.date.today()
    times = ["08:00:00", "14:00:00", "20:00:00"]
    
    while True:
        str_date = current_date.strftime("%d/%m/%Y")
        if str_date not in scheduled_dates:
            scheduled_dates[str_date] = []

        for time in times:
            if time not in scheduled_dates[str_date]:
                scheduled_dates[str_date].append(time)
                write_scheduled_dates(scheduled_dates)
                return datetime.datetime.strptime(str_date + " " + time, "%d/%m/%Y %H:%M:%S")

        current_date += datetime.timedelta(days=1)

def get_flag_image_path(country_code, country_flags):
    flag_unicode = country_flags.get(country_code.upper(), {}).get('unicode')
    if flag_unicode:
        flag_filename = flag_unicode.replace(' ', '-').replace('U+', '') + '.svg'
        return os.path.join(FLAGS_FOLDER_PATH, flag_filename)
    return None

def get_flag_emoji(country_code):
    with open(COUNTRY_FLAGS_FILE, 'r') as file:
        country_flags = json.load(file)
    country_data = country_flags.get(country_code.upper())
    if country_data:
        return country_data['emoji']
    return "🏳️"

def get_levels(game_id):
    response = api_get(f"games/{game_id}/levels")
    if response and 'data' in response:
        return {level['id']: level['name'] for level in response['data']}
    return {}

def get_games():
    response = api_get("games")
    if response:
        return {game['id']: game['names']['international'] for game in response['data']}
    return {}

def get_player_info(player_id):
    response = api_get(f"users/{player_id}")
    if response:
        player = response['data']
        location = player.get('location') or {}
        country = location.get('country') or {}
        country_code = country.get('code', 'Unknown')
        return player['names']['international'], country_code
    return "Unknown", "Unknown"

def is_game_active(game_id):
    return True

def get_category_name(category_id):
    response = api_get(f"categories/{category_id}")
    if response:
        return response['data']['name']
    return "Unknown"

def get_top_run_from_category(game_id, category_id, game_name):
    category_response = api_get(f"categories/{category_id}")
    if not category_response or 'data' not in category_response:
        print(f"Erreur de récupération des informations de la catégorie {category_id}")
        return None

    category_type = category_response['data'].get('type')
    if category_type == 'per-level':
        levels_response = get_levels(game_id)
        if not levels_response:
            print(f"Aucun niveau trouvé pour le jeu {game_id}")
            return None

        for level_id, level_name in levels_response.items():
            leaderboard_url = f"leaderboards/{game_id}/level/{level_id}/{category_id}?top=1"
            leaderboard_response = api_get(leaderboard_url)
            if leaderboard_response and 'runs' in leaderboard_response['data'] and leaderboard_response['data']['runs']:
                top_run_data = leaderboard_response['data']['runs'][0]['run']
                if is_run_valid(top_run_data):
                    return extract_run_data(top_run_data, game_name, level_name + " - " + category_response['data']['name'])

    elif category_type == 'per-game':
        leaderboard_url = f"leaderboards/{game_id}/category/{category_id}?top=1"
        leaderboard_response = api_get(leaderboard_url)
        if leaderboard_response and 'runs' in leaderboard_response['data'] and leaderboard_response['data']['runs']:
            top_run_data = leaderboard_response['data']['runs'][0]['run']
            if is_run_valid(top_run_data):
                return extract_run_data(top_run_data, game_name, category_response['data']['name'])

    return None

def is_run_valid(run_data):
    run_duration = run_data.get('times', {}).get('primary_t', 0)
    return run_duration <= 300

def extract_run_data(run_data, game_name, category_name):
    player_id = run_data['players'][0]['id']
    player_name, country_code = get_player_info(player_id)
    
    run_link = run_data.get('weblink')
    player_profile_link = f"https://www.speedrun.com/user/{player_name}"

    return {
        'game_name': game_name,
        'category_name': category_name,
        'player_name': player_name,
        'country': country_code,
        'date': run_data.get('date', 'Unknown'),
        'video_url': run_data.get('videos', {}).get('links', [{}])[0].get('uri', ''),
        'run_link': run_link,
        'player_profile_link': player_profile_link
    }

def safe_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '', filename)

def download_video(video_url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s-%(id)s.%(ext)s'),
        'noplaylist': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        downloaded_video_path = ydl.prepare_filename(info_dict)
    video_id = get_video_id_from_url(video_url)
    return downloaded_video_path, video_id

def main():
    games = get_games()
    used_runs_db = {}
    downloaded_urls = set()
    api_cache = {}
    youtube = create_youtube_client(client_secrets_file, scopes)

    with open(COUNTRY_FLAGS_FILE, 'r') as file:
        country_flags = json.load(file)

    if os.path.exists(USED_RUNS_DB_FILE):
        with open(USED_RUNS_DB_FILE, "r") as file:
            used_runs_db = json.load(file)

    processed_videos = 0
    while processed_videos < 3:
        game_id, game_name = random.choice(list(games.items()))
        if is_game_active(game_id):
            categories_response = api_get(f"games/{game_id}/categories")
            if categories_response is not None and 'data' in categories_response:
                categories = categories_response['data']
                for category in categories:
                    category_id = category['id']
                    if category_id not in used_runs_db.get(game_id, {}):
                        top_run = get_top_run_from_category(game_id, category_id, game_name)
                        if top_run and top_run['video_url']:
                            video_id = get_video_id_from_url(top_run['video_url'])
                            if video_id not in used_runs_db.get(game_id, {}).get(category_id, []):
                                video_path, video_id = download_video(top_run['video_url'])
                                final_video_path = process_video(video_path, top_run, country_flags)
                                if final_video_path:
                                    upload_video(final_video_path, top_run)
                                    update_used_runs_db(game_id, category_id, video_id)

                                    post_time = get_next_available_slot()
                                    update_scheduled_dates(post_time)

                                    processed_videos += 1
                                    downloaded_urls.add(top_run['video_url'])
            else:
                print(f"Erreur lors de la récupération des catégories pour le jeu {game_id}")

    with open(USED_RUNS_DB_FILE, "w") as file:
        json.dump(used_runs_db, file, indent=4)

if __name__ == "__main__":
    main()

