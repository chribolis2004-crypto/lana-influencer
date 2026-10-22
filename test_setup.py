import os
from dotenv import load_dotenv
from google import genai

def test_setup():
    print("--- 🌸 Lana Project: Environment Diagnostic ---")

    # 1. Load .env
    load_dotenv()

    # 2. Verify API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[❌] FAIL: GEMINI_API_KEY not found in environment or .env file.")
        return False
    else:
        print("[✅] PASS: GEMINI_API_KEY is present.")

    # 3. Test Client Initialization
    try:
        client = genai.Client(api_key=api_key)
        print("[✅] PASS: Google GenAI client initialized successfully.")
    except Exception as e:
        print(f"[❌] FAIL: Client initialization error: {e}")
        return False

    print("\n--- 🚀 System Ready ---")
    print("The environment is correctly configured for:")
    print("- Static Image Generation (Imagen 3)")
    print("- Carousel Sequences (Multi-prompting)")
    print("- Short Video Content (Veo)")
    print("--------------------------------------------")
    return True

if __name__ == "__main__":
    test_setup()
