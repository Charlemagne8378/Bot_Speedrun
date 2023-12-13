import os
import random
import re
import json
import requests
import yt_dlp as youtube_dl
import cv2

# Variables + Constantes
API_BASE_URL = "https://www.speedrun.com/api/v1"
COUNTRY_FLAGS_FILE = "country_flags.json"
DOWNLOAD_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_download"
FINAL_VIDEO_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_final"
USED_RUNS_DB_FILE = "used_runs_db.json"

def get_flag_emoji(country_code):
    with open(COUNTRY_FLAGS_FILE, 'r') as file:
        country_flags = json.load(file)
    country_data = country_flags.get(country_code.upper())
    if country_data:
        return country_data['emoji']
    return "🏳️"  # Default flag for unknown country codes

############################

def api_get(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error in API request: {e}")
        return None

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
    response = api_get(f"leaderboards/{game_id}/category/{category_id}?top=1")
    if response and 'runs' in response['data'] and response['data']['runs']:
        category_name = get_category_name(category_id)
        top_run_data = response['data']['runs'][0]['run']
        player_id = top_run_data['players'][0]['id']
        player_name, country_code = get_player_info(player_id)

        return {
            'game_name': game_name,
            'category_name': category_name,
            'player_name': player_name,
            'country': country_code,
            'date': top_run_data.get('date', 'Unknown'),
            'video_url': top_run_data.get('videos', {}).get('links', [{}])[0].get('uri', '')
        }
    return None

def safe_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '', filename)

def download_video(video_url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        'noplaylist': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        downloaded_video_path = ydl.prepare_filename(info_dict)
    return downloaded_video_path

def process_video(video_path, run_info):
    country_flag = get_flag_emoji(run_info['country'])
    text_content = f"{run_info['player_name']} {country_flag}\n{run_info['game_name']}\n{run_info['category_name']}\n{run_info['date']}"

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video: {video_path}")
        return

    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(os.path.join(FINAL_VIDEO_PATH, safe_filename(run_info['game_name'] + '.mp4')), fourcc, cap.get(cv2.CAP_PROP_FPS), (orig_width, orig_height))

    font = cv2.FONT_HERSHEY_SIMPLEX
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Apply text to the frame
        y0, dy = 50, 40
        for i, line in enumerate(text_content.split('\n')):
            cv2.putText(frame, line, (50, y0 + i * dy), font, 1, (255, 255, 255), 2)

        out.write(frame)

    cap.release()
    out.release()


def main():
    games = get_games()
    used_runs_db = {}
    if os.path.exists(USED_RUNS_DB_FILE):
        with open(USED_RUNS_DB_FILE, "r") as file:
            used_runs_db = json.load(file)

    try_count = 0
    while try_count < 3:
        game_id, game_name = random.choice(list(games.items()))
        categories = api_get(f"games/{game_id}/categories")['data']
        for category in categories:
            if category['id'] not in used_runs_db.get(game_id, []):
                top_run = get_top_run_from_category(game_id, category['id'], game_name)
                if top_run and top_run['video_url']:
                    video_path = download_video(top_run['video_url'])
                    process_video(video_path, top_run)
                    used_runs_db.setdefault(game_id, []).append(category['id'])
                    break
        try_count += 1

    with open(USED_RUNS_DB_FILE, "w") as file:
        json.dump(used_runs_db, file)

if __name__ == "__main__":
    main()
