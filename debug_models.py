
import os
from google import genai
try:
    print("Initializing client...")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    print("Listing models...")
    for m in client.models.list():
        if "gemini" in m.name:
            print(f"- {m.name} ({m.display_name})")
except Exception as e:
    print(f"Error: {e}")
