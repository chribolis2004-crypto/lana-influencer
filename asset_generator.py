import os
import pandas as pd
import yaml
from google import genai
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Google GenAI client (Uses GEMINI_API_KEY from env)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def load_brand_bible():
    with open('brand_bible.yaml', 'r') as f:
        return yaml.safe_load(f)

def get_enriched_prompt(visual_prompt, brand_bible, variation=""):
    identity = brand_bible['brand_bible']['visual_identity']
    base = (
        f"High-end professional photography of {identity['influencer_name']}. "
        f"Physical characteristics: {identity['face_reference']}, {identity['hair']}. "
        f"Overall style: {identity['style']}. Lighting: {identity['lighting']}. "
    )
    detail = f"Scene details: {visual_prompt}. {variation}"
    footer = "8k resolution, cinematic, photorealistic, high fashion magazine quality, extreme detail."
    return f"{base} {detail} {footer}"

def generate_single_image(prompt):
    try:
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=genai.types.GenerateImagesConfig(number_of_images=1)
        )
        return response.generated_images[0].image.bytes
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

def generate_video(prompt):
    try:
        # Veo / Video generation endpoint via google-genai
        # Note: Video generation is often asynchronous.
        # This implementation assumes a synchronous-like response or a path provided by the API.
        response = client.models.generate_content(
            model='veo-1', # Hypothetical model ID for Veo
            contents=[prompt]
        )
        # Assuming the response provides bytes or a downloadable file
        # Since Veo API specs can vary, we simulate the retrieval of bytes
        if hasattr(response, 'video_bytes'):
            return response.video_bytes
        # Fallback for certain SDK versions where it might be in a different attribute
        return getattr(response, 'data', None)
    except Exception as e:
        print(f"Error generating video with Veo: {e}")
        return None

def save_asset(asset_bytes, filename):
    try:
        with open(filename, 'wb') as f:
            f.write(asset_bytes)
        return True
    except Exception as e:
        print(f"Error saving asset {filename}: {e}")
    return False

def process_assets():
    bible = load_brand_bible()
    df = pd.read_csv('content_calendar.csv')

    if 'content_id' not in df.columns:
        df['content_id'] = [f"LAN_{100 + i}" for i in range(len(df))]
        df.to_csv('content_calendar.csv', index=False)

    generated_count = 0

    for index, row in df.iterrows():
        if row['qa_status'] == 'approved' and (pd.isna(row['image_path']) or row['image_path'] == ""):
            fmt = str(row['format']).lower()
            cid = row['content_id']

            if fmt == 'carousel':
                print(f"Generating carousel for {cid}...")
                variations = [
                    "Wide shot, full body pose.",
                    "Medium shot, focusing on outfit details.",
                    "Close-up shot, focusing on accessories and expression."
                ]
                paths = []
                for i, var in enumerate(variations):
                    prompt = get_enriched_prompt(row['visual_prompt'], bible, var)
                    img_bytes = generate_single_image(prompt)
                    if img_bytes:
                        fname = f"assets/{cid}_slide{i+1}.png"
                        if save_asset(img_bytes, fname):
                            paths.append(fname)

                if paths:
                    df.at[index, 'image_path'] = ",".join(paths)
                    df.at[index, 'production_status'] = 'ready'
                    generated_count += 1

            elif fmt == 'short_video':
                print(f"Generating short video for {cid}...")
                prompt = get_enriched_prompt(row['visual_prompt'], bible, "Dynamic movement, cinematic pan, 4k video.")
                vid_bytes = generate_video(prompt)
                if vid_bytes:
                    fname = f"assets/{cid}.mp4"
                    if save_asset(vid_bytes, fname):
                        df.at[index, 'image_path'] = fname
                        df.at[index, 'production_status'] = 'ready'
                        generated_count += 1

            else: # Single image / default
                print(f"Generating image for {cid}...")
                prompt = get_enriched_prompt(row['visual_prompt'], bible)
                img_bytes = generate_single_image(prompt)
                if img_bytes:
                    fname = f"assets/{cid}.png"
                    if save_asset(img_bytes, fname):
                        df.at[index, 'image_path'] = fname
                        df.at[index, 'production_status'] = 'ready'
                        generated_count += 1

    df.to_csv('content_calendar.csv', index=False)
    print(f"Asset generation complete. {generated_count} records updated.")

if __name__ == "__main__":
    process_assets()
