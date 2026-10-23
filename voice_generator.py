import os
import requests
import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

def generate_voice(text, voice_id, creator_name, filename=None):
    """
    Converts text to speech using Fish Audio API.
    Saves the output to the creator's assets folder.
    """
    api_key = os.environ.get("FISH_API_KEY")
    if not api_key:
        print("Error: FISH_API_KEY not found in environment variables.")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            # Determine save path
            if not filename:
                filename = "voice_asset.mp3"

            asset_path = os.path.join("creators", creator_name, "assets", filename)
            os.makedirs(os.path.dirname(asset_path), exist_ok=True)

            with open(asset_path, "wb") as f:
                f.write(response.content)

            print(f"Successfully generated audio: {asset_path}")
            return asset_path
        else:
            print(f"Fish Audio API Error ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"Unexpected error during voice generation: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fish Audio Voice Generator")
    parser.add_argument("--creator", type=str, help="Name of the creator")
    parser.add_argument("--text", type=str, help="Text to synthesize")
    parser.add_argument("--voice_id", type=str, help="Fish Audio Voice ID")
    parser.add_argument("--test", action="store_true", help="Run a quick test generation")
    parser.add_argument("--filename", type=str, help="Custom filename for the audio file")

    args = parser.parse_args()

    if args.test:
        # Test mode: uses a generic creator name or 'test' to save the file
        text = "Ciao! Questo è un test della mia nuova voce. Spero che vi piaccia!"
        voice_id = args.voice_id or "21m00Tcm4TlvDq8ikWAM" # Default placeholder
        creator = "test_voice"
        filename = "test_voice.mp3"
        generate_voice(text, voice_id, creator, filename)
    elif args.creator and args.text and args.voice_id:
        generate_voice(args.text, args.voice_id, args.creator, args.filename)
    else:
        print("Missing required arguments. Use --help for usage.")
        sys.exit(1)
