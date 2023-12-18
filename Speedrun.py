import os
import random
import re
import json
import requests
import yt_dlp
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cairosvg
from io import BytesIO
from urllib.parse import urlparse, parse_qs

# Variables + Constantes
API_BASE_URL = "https://www.speedrun.com/api/v1"
USED_RUNS_DB_FILE = "used_runs_db.json"
DOWNLOAD_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_download"
FINAL_VIDEO_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_final"
FLAGS_FOLDER_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\flags"
FONT_PATH = "arial.ttf"

def api_get(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erreur de réponse de l'API : Code de statut {response.status_code} pour {endpoint}")
    except requests.RequestException as e:
        print(f"Erreur de requête de l'API : {e}")
    return None

def get_video_id_from_url(video_url):
    parsed_url = urlparse(video_url)
    if "youtube" in parsed_url.netloc:
        return parse_qs(parsed_url.query)['v'][0]
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

def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    cap.release()
    return duration

def convert_svg_to_png(svg_path):
    png_image = cairosvg.svg2png(url=svg_path)
    return Image.open(BytesIO(png_image))

def process_video(video_path, run_info, tiktok=True):
    max_segment_duration = 61 if tiktok else 59
    output_folder = os.path.join(FINAL_VIDEO_PATH if tiktok else r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_YT", safe_filename(f"{run_info['game_name']} - {run_info['category_name']}"))

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video: {video_path}")
        return None

    # Extraction d'une image pour l'arrière-plan flou
    ret, background_frame = cap.read()
    if not ret:
        print("Error reading the first frame for background.")
        return None

    # Application d'un flou gaussien sur l'image de fond
    background_frame = cv2.GaussianBlur(background_frame, (21, 21), 0)
    background_frame_resized = cv2.resize(background_frame, (720, 1280))

    fps = cap.get(cv2.CAP_PROP_FPS)
    segment_duration_frames = int(max_segment_duration * fps)

    segment_paths = []
    segment_count = 0
    total_frames_processed = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    while total_frames_processed < total_frames:
        segment_name = f"{run_info['game_name']} - {run_info['category_name']} - {run_info['player_name']} - {'TikTok' if tiktok else 'YouTube'} Part {segment_count + 1}.mp4"
        segment_path = os.path.join(output_folder, safe_filename(segment_name))
        segment_paths.append(segment_path)

        out = cv2.VideoWriter(segment_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (720, 1280))

        for _ in range(segment_duration_frames):
            if total_frames_processed >= total_frames:
                break
            ret, frame = cap.read()
            if not ret:
                break

            # Redimensionnement et placement de la vidéo sur l'arrière-plan flou
            frame_resized = cv2.resize(frame, (720, 1280 - 2 * int((1280 - 720 * 9 / 16) / 2)))
            y_offset = int((1280 - 720 * 9 / 16) / 2)
            final_frame = background_frame_resized.copy()
            final_frame[y_offset:y_offset + frame_resized.shape[0], :] = frame_resized

            frame_pil = Image.fromarray(cv2.cvtColor(final_frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(frame_pil)
            font = ImageFont.truetype(FONT_PATH, 42)

            # Ajout de l'ombre au texte
            shadow_offset = 2
            text_content = f"{run_info['player_name']}\n{run_info['game_name'].strip()}\n{run_info['category_name']}\n{run_info['date']}"
            shadow_position = (50 + shadow_offset, 50 + shadow_offset)
            draw.text(shadow_position, text_content, font=font, fill="black")

            # Dessin du texte principal
            text_position = (50, 50)
            draw.text(text_position, text_content, font=font, fill="white")

            flag_path = get_flag_image_path(run_info['country'])
            if os.path.exists(flag_path):
                flag_image = convert_svg_to_png(flag_path).resize((80, 70))
                frame_pil.paste(flag_image, (300, 40), flag_image)

            final_frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
            out.write(final_frame)

            total_frames_processed += 1

        out.release()
        segment_count += 1

    cap.release()
    return segment_paths

def get_flag_image_path(country_code):
    return os.path.join(FLAGS_FOLDER_PATH, f"{country_code.lower()}.svg")

def safe_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '', filename)

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
                    run_duration = top_run_data.get('times', {}).get('primary_t', 0)
                    return extract_run_data(top_run_data, game_name, level_name + " - " + category_response['data']['name'], run_duration)

    elif category_type == 'per-game':
        leaderboard_url = f"leaderboards/{game_id}/category/{category_id}?top=1"
        leaderboard_response = api_get(leaderboard_url)
        if leaderboard_response and 'runs' in leaderboard_response['data'] and leaderboard_response['data']['runs']:
            top_run_data = leaderboard_response['data']['runs'][0]['run']
            if is_run_valid(top_run_data):
                run_duration = top_run_data.get('times', {}).get('primary_t', 0)
                return extract_run_data(top_run_data, game_name, category_response['data']['name'], run_duration)

    return None

def is_run_valid(run_data):
    run_duration = run_data.get('times', {}).get('primary_t', 0)
    return 10 <= run_duration <= 300

def extract_run_data(run_data, game_name, category_name, run_duration):
    if 'players' in run_data and run_data['players']:
        player_info = run_data['players'][0]
        if 'id' in player_info:
            player_id = player_info['id']
            player_name, country_code = get_player_info(player_id)
        else:
            player_name = "Unknown Player"
            country_code = "Unknown"
    else:
        player_name = "Unknown Player"
        country_code = "Unknown"

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
        'player_profile_link': player_profile_link,
        'duration': run_duration
    }

def download_video(video_url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s-%(id)s.%(ext)s'),
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        downloaded_video_path = ydl.prepare_filename(info_dict)
    video_id = get_video_id_from_url(video_url)
    return downloaded_video_path, video_id

def create_description_file(run_info, folder_path):
    description_template = (
        "Check out this incredible speedrun!\n"
        "What do you think?\n"
        "TikTok: https://www.tiktok.com/@speedrunspectre\n"
        "Instagram: https://www.instagram.com/speedrunspectre/\n"
        "Run Link: {run_link}\n"
        "Player Profile: {player_profile_link}\n"
        "Player: {player_name}\n"
        "Game: {game_name}\n"
        "Category: {category_name}\n"
        "Date: {date}\n"
    )

    description = description_template.format(
        run_link=run_info['run_link'],
        player_profile_link=run_info['player_profile_link'],
        player_name=run_info['player_name'],
        game_name=run_info['game_name'],
        category_name=run_info['category_name'],
        date=run_info['date']
    )

    description_file_path = os.path.join(folder_path, 'description.txt')
    with open(description_file_path, 'w') as file:
        file.write(description)

    return description_file_path

def read_game_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def extract_game_id_from_url(url):
    return url.split('/')[-1]

def main():
    game_urls_file = r"A:\Dossiers\Documents\SpeedRun_tiktok\game_urls.txt"
    game_urls = read_game_urls(game_urls_file)
    used_runs_db = {}

    if os.path.exists(USED_RUNS_DB_FILE):
        with open(USED_RUNS_DB_FILE, "r") as file:
            used_runs_db = json.load(file)

    processed_videos = 0
    while processed_videos < 10000:
        random_game_url = random.choice(game_urls)
        game_id = extract_game_id_from_url(random_game_url)

        game_name_response = api_get(f"games/{game_id}")
        if not game_name_response or 'data' not in game_name_response:
            print(f"Erreur lors de la récupération du nom pour le jeu {game_id}")
            continue

        game_name = game_name_response['data']['names']['international']

        categories_response = api_get(f"games/{game_id}/categories")
        if not categories_response or 'data' not in categories_response:
            continue

        for category in categories_response['data']:
            category_id = category['id']
            if category_id in used_runs_db.get(game_id, {}):
                continue

            top_run = get_top_run_from_category(game_id, category_id, game_name)
            if not top_run or not top_run['video_url']:
                continue

            video_id = get_video_id_from_url(top_run['video_url'])
            if video_id in used_runs_db.get(game_id, {}).get(category_id, []):
                continue

            if "youtube.com" in top_run['video_url'] or "twitch.tv" in top_run['video_url'] or "youtu.be" in top_run['video_url']:
                video_path, video_id = download_video(top_run['video_url'])
                video_duration = get_video_duration(video_path)

                if video_duration <= top_run['duration'] + 120:
                    final_video_paths_tiktok = process_video(video_path, top_run, tiktok=True)
                    final_video_paths_youtube = process_video(video_path, top_run, tiktok=False)
                    print(f"Processed video for TikTok and YouTube: {video_path}")
                    processed_videos += 1

                update_used_runs_db(game_id, category_id, video_id)
            else:
                print(f"Skipping non-YouTube/Twitch video: {top_run['video_url']}")
                update_used_runs_db(game_id, category_id, video_id)

            if processed_videos >= 10000:
                break

        if processed_videos >= 10000:
            break

    with open(USED_RUNS_DB_FILE, "w") as file:
        json.dump(used_runs_db, file, indent=4)

if __name__ == "__main__":
    main()
