import os
import pandas as pd
import yaml
import json
import time
import argparse
import sys
from google import genai
import io
from dotenv import load_dotenv
from fish_audio_sdk import FishAudio
from voice_generator import generate_voice

# Load environment variables from .env file
load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="Multi-influencer Asset Generator")
    parser.add_argument("--creator", type=str, required=True, help="Name of the creator to generate assets for")
    return parser.parse_args()

# --- LOGGING SYSTEM ---
class Logger:
    def __init__(self, creator_name):
        self.log_dir = os.path.join("creators", creator_name)
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "generation.log")

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        # Use sys.__stdout__.write to avoid recursion when stdout is redirected
        sys.__stdout__.write(formatted_msg + "\n")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(formatted_msg + "\n")

# Replace built-in print with Logger
def setup_logger(creator_name):
    logger = Logger(creator_name)
    # Override sys.stdout to capture all prints
    class LogStream:
        def write(self, message):
            if message.strip():
                logger.log(message.strip())
        def flush(self):
            pass
    sys.stdout = LogStream()
    return logger

# Initialize Google GenAI client (Uses GEMINI_API_KEY from env)
def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    return genai.Client(api_key=api_key)

def load_brand_bible(creator_path):
    bible_path = os.path.join(creator_path, 'brand_bible.yaml')
    if not os.path.exists(bible_path):
        print(f"Brand bible not found for creator at {bible_path}")
        return {}
    with open(bible_path, 'r') as f:
        return yaml.safe_load(f)

def get_enriched_prompt(visual_prompt, brand_bible, variation="", voice_tuning=None):
    # Handle empty bible
    if not brand_bible:
        return f"{visual_prompt} {variation}"

    try:
        identity = brand_bible['brand_bible']['visual_identity']
    except (KeyError, TypeError):
        return f"{visual_prompt} {variation}"

    # GROWTH ENGINE: Cinematic and Social-First Visual Directives
    # We move from 'what to show' to 'how to film it for retention'
    cinematic_directives = (
        "CAMERA: Use dynamic angles (Dutch angle, extreme close-ups, rapid cuts). "
        "EXPRESSIONS: Micro-expressions of confidence, irony, or surprise. "
        "VISUAL CUES: Incorporate kinetic typography placeholders and visual tension. "
        "PACING: High-energy composition that implies movement and rapid transitions. "
    )

    base = (
        f"High-end professional cinematography of {identity['influencer_name']}. "
        f"Physical characteristics: {identity['face_reference']}, {identity['hair']}. "
        f"Overall style: {identity['style']}. Lighting: {identity['lighting']}. "
    )

    # Brand Voice Tuning Integration
    voice_addition = ""
    if voice_tuning:
        irony = voice_tuning.get("irony", 50)
        emoji = voice_tuning.get("emoji_frequency", 50)
        tone = voice_tuning.get("tone", "Neutral")

        irony_level = "Low" if irony < 33 else "Medium" if irony < 66 else "High"
        emoji_level = "Low" if emoji < 33 else "Medium" if emoji < 66 else "High"

        voice_addition = f" Mood/Tone: {tone}, Irony level: {irony_level}, Emoji frequency: {emoji_level}. "

    detail = f"{cinematic_directives} Scene details: {visual_prompt}. {variation} {voice_addition}"
    footer = "8k resolution, cinematic, photorealistic, high fashion magazine quality, extreme detail, social-first composition, high retention framing."
    return f"{base} {detail} {footer}"

def safe_generate_image(client, prompt, creator_path):
    while True:
        try:
            # REFERENCE IMAGE INTEGRATION
            # Load the reference image if it exists to ensure visual consistency
            ref_path = os.path.join(creator_path, "assets", "reference.png")
            image_input = None
            if os.path.exists(ref_path):
                with open(ref_path, "rb") as f:
                    image_input = genai.types.Part.from_bytes(
                        data=f.read(),
                        mime_type="image/png"
                    )

            # Construct the multimodal prompt
            # If we have a reference image, we pass both the image and the text
            if image_input:
                response = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=prompt,
                    config=genai.types.GenerateImagesConfig(
                        number_of_images=1,
                        # Pass the reference image as a conditioning input
                        # Note: API specific parameter names may vary based on SDK version
                        reference_images=[image_input]
                    )
                )
            else:
                response = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=prompt,
                    config=genai.types.GenerateImagesConfig(number_of_images=1)
                )
            return response.generated_images[0].image.bytes
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "quota" in err_msg or "exhausted" in err_msg:
                log_message(creator_path, f"Rate limit hit: {e}. Sleeping for 60 seconds...")
                time.sleep(60)
                continue
            else:
                log_message(creator_path, f"Unexpected error during image generation: {e}")
                return None


def safe_generate_video(client, prompt):
    while True:
        try:
            # Veo / Video generation endpoint via google-genai
            response = client.models.generate_content(
                model='veo-1',
                contents=[prompt]
            )
            # Simulation of bytes retrieval
            if hasattr(response, 'video_bytes'):
                return response.video_bytes
            return getattr(response, 'data', None)
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "quota" in err_msg or "exhausted" in err_msg:
                print(f"Rate limit hit: {e}. Sleeping for 60 seconds...")
                time.sleep(60)
                continue
            else:
                print(f"Unexpected error during video generation: {e}")
                return None

def save_asset(asset_bytes, filename):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(asset_bytes)
        return True
    except Exception as e:
        print(f"Error saving asset {filename}: {e}")
    return False

def process_assets(creator_name):
    # Setup logging
    setup_logger(creator_name)

    # Setup paths
    creator_path = os.path.join("creators", creator_name)
    calendar_path = os.path.join(creator_path, "calendar.csv")
    assets_path = os.path.join(creator_path, "assets")
    config_path = os.path.join(creator_path, "config.json")

    if not os.path.exists(calendar_path):
        print(f"No calendar found for creator {creator_name}")
        return

    # Load voice tuning from config
    voice_tuning = None
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            voice_tuning = config.get("voice_tuning")

    bible = load_brand_bible(creator_path)
    df = pd.read_csv(calendar_path)

    if 'content_id' not in df.columns:
        df['content_id'] = [f"{creator_name[:3].upper()}_{100 + i}" for i in range(len(df))]
        df.to_csv(calendar_path, index=False)

    client = get_client()
    generated_count = 0

    for index, row in df.iterrows():
        # We generate assets for items that are approved at the proposal stage and don't have an image yet
        if row['qa_status'] == 'approved' and (pd.isna(row['image_path']) or row['image_path'] == ""):
            fmt = str(row['format']).lower()
            cid = row['content_id']

            # Use relative path for storage in the CSV
            relative_asset_path = ""

            # VOICE GENERATION: Generate audio if a Voice ID is configured and the format is video or a specific audio format
            voice_id = config.get("fish_audio_voice_id") if config else None
            if voice_id and (fmt == 'short_video' or 'audio' in fmt):
                print(f"Generating voice with Fish Audio for {cid}...")
                fish = FishAudio(api_key=os.getenv("FISH_API_KEY"))
                try:
                    # Using the Fish Audio SDK to generate speech
                    # We assume generate_speech returns something that can be saved or a path
                    audio_result = fish.generate_speech(
                        text=row['caption'],
                        voice_id=voice_id
                    )
                    audio_filename = f"{cid}_voice.mp3"
                    full_audio_path = os.path.join(assets_path, audio_filename)
                    with open(full_audio_path, "wb") as f:
                        f.write(audio_result)
                    print(f"Voice generated: {full_audio_path}")
                except Exception as e:
                    print(f"Fish Audio generation failed for {cid}: {e}")

            if fmt == 'carousel':
                print(f"Generating carousel for {cid}...")
                variations = [
                    "Wide shot, full body pose.",
                    "Medium shot, focusing on outfit details.",
                    "Close-up shot, focusing on accessories and expression."
                ]
                paths = []
                for i, var in enumerate(variations):
                    prompt = get_enriched_prompt(row['visual_prompt'], bible, var, voice_tuning)
                    # Pass creator_path to the generation function to allow reference image loading
                    img_bytes = safe_generate_image(client, prompt, creator_path)

                    if img_bytes:
                        fname = f"{cid}_slide{i+1}.png"
                        full_path = os.path.join(assets_path, fname)
                        if save_asset(img_bytes, full_path):
                            paths.append(fname)

                if paths:
                    relative_asset_path = ",".join(paths)
                    df.at[index, 'image_path'] = relative_asset_path
                    df.at[index, 'production_status'] = 'ready'
                    generated_count += 1

            elif fmt == 'short_video':
                print(f"Generating short video for {cid}...")
                prompt = get_enriched_prompt(row['visual_prompt'], bible, "Dynamic movement, cinematic pan, 4k video.", voice_tuning)
                vid_bytes = safe_generate_video(client, prompt)
                if vid_bytes:
                    fname = f"{cid}.mp4"
                    full_path = os.path.join(assets_path, fname)
                    if save_asset(vid_bytes, full_path):
                        relative_asset_path = fname
                        df.at[index, 'image_path'] = relative_asset_path
                        df.at[index, 'production_status'] = 'ready'
                        generated_count += 1

            else: # Single image / default
                print(f"Generating image for {cid}...")
                prompt = get_enriched_prompt(row['visual_prompt'], bible, voice_tuning=voice_tuning)
                # Pass creator_path to the generation function to allow reference image loading
                img_bytes = safe_generate_image(client, prompt, creator_path)

                if img_bytes:
                    fname = f"{cid}.png"
                    full_path = os.path.join(assets_path, fname)
                    if save_asset(img_bytes, full_path):
                        relative_asset_path = fname
                        df.at[index, 'image_path'] = relative_asset_path
                        df.at[index, 'production_status'] = 'ready'
                        generated_count += 1

            # IMMEDIATE SAVE after every successful asset generation
            df.to_csv(calendar_path, index=False)

    print(f"Asset generation complete for {creator_name}. {generated_count} records updated.")

if __name__ == "__main__":
    args = parse_args()
    process_assets(args.creator)
