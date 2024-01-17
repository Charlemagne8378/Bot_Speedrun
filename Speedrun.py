import os
import random
import re
import json
import requests
from urllib.parse import urlparse, parse_qs
import yt_dlp
import cv2
import numpy as np
from PIL import Image
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ImageClip
from moviepy.config import change_settings

# Configuration pour ImageMagick (ajustez si nécessaire)
change_settings({
    "IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
    "FFMPEG_BINARY": "ffmpeg",
    "TEMP_FILE_DIR": r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_TEMP"  # Répertoire temporaire spécifié
})

# CONSTANTES
API_BASE_URL = "https://www.speedrun.com/api/v1"
USED_RUNS_DB_FILE = "used_runs_db.json"
DOWNLOAD_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_download"
FINAL_VIDEO_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_final"
FLAGS_FOLDER_PATH = r"A:\Dossiers\Documents\SpeedRun_tiktok\flags"

# Fonctions d'assistance API
def api_get(endpoint):
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erreur lors de l'accès à {url}: {e}")
        return None

def get_game_name(game_id):
    response = api_get(f"games/{game_id}")
    return response['data']['names']['international']

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

def capture_random_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames_to_capture = [random.randint(0, frame_count - 1) for _ in range(2)]  # Exemple : 2 images

    frames = []
    for frame_no in frames_to_capture:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        success, frame = cap.read()
        if success:
            frames.append(frame)

    cap.release()
    return frames

def resize_frame_to_banner(frame, banner_height):
    height, width, _ = frame.shape
    aspect_ratio = width / height
    new_width = int(banner_height * aspect_ratio)
    resized_frame = cv2.resize(frame, (new_width, banner_height), interpolation=cv2.INTER_AREA)
    return resized_frame

def add_banner_images_to_video(segment_clip, banner_images, banner_height):
    for i, banner_image in enumerate(banner_images):
        pil_banner_image = Image.fromarray(banner_image)
        position = ("left", "bottom") if i == 0 else ("right", "bottom")
        banner_clip = ImageClip(np.array(pil_banner_image)).set_duration(segment_clip.duration).set_position(position)
        segment_clip = CompositeVideoClip([segment_clip, banner_clip])

    return segment_clip

#########################################################################################
def get_flag_image_path(country_code):
    if country_code.lower() == "unknown":
        return None
    return os.path.join(FLAGS_FOLDER_PATH, f"{country_code.lower()}.png")

def get_flag_image_clip(flag_png_path, duration):
    pil_image = Image.open(flag_png_path)
    np_image = np.array(pil_image)
    image_clip = ImageClip(np_image, duration=duration)
    image_clip = image_clip.resize(height=100).set_position(("right", "bottom"))
    return image_clip


def select_random_game(game_urls):
    random_game_url = random.choice(game_urls)
    game_id = random_game_url.split('/')[-1]
    return game_id


#########################################################################################

def safe_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '', filename)

def apply_gaussian_blur(image, blur_strength=15):
    return cv2.GaussianBlur(image, (blur_strength, blur_strength), 0)

def capture_frame(video_path, frame_number=0):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    success, frame = cap.read()
    cap.release()
    return frame if success else None

def process_video(video_path, run_info):
    try:
        # Charger la vidéo source
        clip = VideoFileClip(video_path)
        audio = clip.audio
        audio_temp_path = os.path.join(r"A:\Dossiers\Documents\SpeedRun_tiktok\Video_TEMP", "temp_audio.mp3")
        audio.write_audiofile(audio_temp_path)

        # Dimensions originales de la vidéo
        original_width, original_height = clip.size
        original_aspect_ratio = original_width / original_height

        # Définir les dimensions cibles pour le format 9:16
        target_width = 720  # Largeur standard pour 9:16
        target_height = 1280  # Hauteur standard pour 9:16

        # Calculer les nouvelles dimensions pour conserver le rapport d'aspect original
        if original_aspect_ratio > (9 / 16):
            # Pour les vidéos plus larges que 9:16, ajuster la largeur
            new_width = target_width
            new_height = int(new_width / original_aspect_ratio)
        else:
            # Pour les vidéos plus hautes que 9:16, ajuster la hauteur
            new_height = target_height
            new_width = int(new_height * original_aspect_ratio)

        # Assurer que la largeur et la hauteur sont divisibles par 2
        new_width += new_width % 2
        new_height += new_height % 2

        # Redimensionner la vidéo
        resized_clip = clip.resize(newsize=(new_width, new_height))

        # Calculer les marges pour les bandes noires
        margin_x = (target_width - new_width) // 2
        margin_y = (target_height - new_height) // 2

        # Ajouter des bandes noires pour obtenir un format 9:16
        final_clip = CompositeVideoClip([resized_clip.set_position((margin_x, margin_y))], size=(target_width, target_height), bg_color=(0, 0, 0))

        # Obtenir une image de la vidéo source
        video_image = clip.get_frame(0)  # Vous pouvez ajuster le temps ici

        # Redimensionner cette image à la même taille que la vidéo
        video_image_resized = cv2.resize(video_image, (target_width, target_height), interpolation=cv2.INTER_AREA)

        # Créer un clip d'image pour cette image
        video_image_clip = ImageClip(np.array(Image.fromarray(cv2.cvtColor(video_image_resized, cv2.COLOR_BGR2RGB))))

        # Ajouter ce clip d'image à votre clip vidéo final
        final_clip = CompositeVideoClip([final_clip, video_image_clip])

        # Durée maximale du segment fixée à 59 secondes
        max_segment_duration = 89
        segment_duration = min(clip.duration, max_segment_duration)
        segment_count = int(clip.duration // segment_duration) + (clip.duration % segment_duration > 0)

        # Dossier de sortie
        segment_folder_name = safe_filename(f"{run_info['player_name']} - {run_info['game_name']} - {run_info['category_name']}")
        output_folder = os.path.join(FINAL_VIDEO_PATH, segment_folder_name)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Traitement de chaque segment
        for i in range(segment_count):
            part_suffix = f" - Part {i + 1}" if segment_count > 1 else ""
            segment_title = f"{run_info['player_name']} - {run_info['game_name']} - {run_info['category_name']}{part_suffix}"
            segment_path = os.path.join(output_folder, f"{segment_title}.mp4")

            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, clip.duration)

            if start_time < clip.duration:
                segment_clip = clip.subclip(start_time, end_time)

                # Redimensionner et positionner le segment
                resized_segment_clip = segment_clip.resize(newsize=(new_width, new_height))
                positioned_clip = CompositeVideoClip([resized_segment_clip.set_position((margin_x, margin_y))], size=(target_width, target_height), bg_color=(0, 0, 0))

                # Ajout du texte
                txt_clip = TextClip(f"Pseudo: {run_info['player_name']}\nJeux: {run_info['game_name']}\nCatégorie: {run_info['category_name']}\nDate: {run_info['date']}",
                                    fontsize=30, color='white', stroke_color='black', stroke_width=0.5, align="West")
                txt_clip = txt_clip.set_position(('left', 'top')).set_duration(positioned_clip.duration)

                # Charger l'image du drapeau
                flag_image_path = get_flag_image_path(run_info['country'])
                if flag_image_path and os.path.exists(flag_image_path):
                    flag_img = ImageClip(flag_image_path).set_duration(positioned_clip.duration).resize(height=50)  # Ajustez la taille selon vos besoins
                    flag_img = flag_img.set_position(("right", "top"))  # Ajustez la position selon vos besoins

                    # Composition de la vidéo finale pour le segment avec le drapeau
                    final_segment_clip = CompositeVideoClip([positioned_clip, txt_clip, flag_img])
                else:
                    # Si l'image du drapeau n'est pas trouvée, continuez sans le drapeau
                    final_segment_clip = CompositeVideoClip([positioned_clip, txt_clip])

                # Écriture du fichier vidéo pour le segment
                final_segment_clip.write_videofile(segment_path, codec="libx264", audio_codec="aac", bitrate="8000k", ffmpeg_params=["-pix_fmt", "yuv420p"])
            else:
                break

        # Création du fichier de description
        create_description_file(run_info, output_folder)

        # Nettoyage des fichiers temporaires
        os.remove(audio_temp_path)

        return output_folder
    except Exception as e:
        print(f"Error processing video: {e}")
        return None

    
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
    return 20 <= run_duration <= 300

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

def read_game_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]
    
def extract_game_id_from_url(url):
    return url.split('/')[-1]

################################################################################################



def download_video(video_url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s-%(id)s.%(ext)s'),
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            downloaded_video_path = ydl.prepare_filename(info_dict)
        video_id = get_video_id_from_url(video_url)
        return downloaded_video_path, video_id
    except Exception as e:
        print(f"Erreur lors du téléchargement de la vidéo : {e}")
        return None, None

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

    description = description_template.format_map(run_info)

    description_file_path = os.path.join(folder_path, 'description.txt')
    with open(description_file_path, 'w') as file:
        file.write(description)

    return description_file_path

def main():
    game_urls_file = r"A:\Dossiers\Documents\SpeedRun_tiktok\game_urls.txt"
    game_urls = read_game_urls(game_urls_file)
    used_runs_db = {}

    if os.path.exists(USED_RUNS_DB_FILE):
        with open(USED_RUNS_DB_FILE, "r") as file:
            used_runs_db = json.load(file)

    processed_videos = 0
    last_game_id = None

    while processed_videos < 10000:
        game_id = select_random_game(game_urls)

        # Assurer que le jeu sélectionné n'est pas le même que le dernier traité
        while game_id == last_game_id:
            game_id = select_random_game(game_urls)

        game_name = get_game_name(game_id)

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
                try:
                    video_path, video_id = download_video(top_run['video_url'])
                    video_duration = get_video_duration(video_path)
                    if video_duration <= top_run['duration'] + 120:
                        process_video(video_path, top_run)
                        processed_videos += 1
                    update_used_runs_db(game_id, category_id, video_id)
                except Exception as e:
                    print(f"Skipping video due to error: {e}")
                    update_used_runs_db(game_id, category_id, video_id)
                    continue
            else:
                print(f"Skipping non-YouTube/Twitch video: {top_run['video_url']}")
                update_used_runs_db(game_id, category_id, video_id)

        # Sauvegarder régulièrement l'état de used_runs_db
        with open(USED_RUNS_DB_FILE, "w") as file:
            json.dump(used_runs_db, file, indent=4)

        last_game_id = game_id  # Mettre à jour le dernier jeu traité

    # Sauvegarde finale de l'état de used_runs_db
    update_used_runs_db(game_id, category_id, video_id)
    print(f"Updated used_runs_db: game_id={game_id}, category_id={category_id}, video_id={video_id}")
    with open(USED_RUNS_DB_FILE, "w") as file:
        json.dump(used_runs_db, file, indent=4)

if __name__ == "__main__":
    main()