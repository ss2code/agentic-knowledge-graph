import os
from google import genai
import sys

def list_models():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("❌ GEMINI_API_KEY not set.")
        return

    print(f"Connecting with key: {key[:5]}...")
    try:
        client = genai.Client(api_key=key)
        # Check docs or inspect client for list_models equivalent in new SDK
        # For google-genai, it is often client.models.list()
        print("Fetching models...")
        # Note: The new SDK might use a different method. 
        # If this fails, we will try the http request method as fallback.
        try:
             # Introspection to find the right method for 0.1.0+ SDKs
             print(f"Inspecting client.models: {dir(client.models)}")
             
             # Try standard list
             if hasattr(client.models, 'list'):
                 for m in client.models.list():
                     print(f"- {m.name}")
             
        except Exception as e_inner:
             print(f"Inner error: {e_inner}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_models()
