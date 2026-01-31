import os
from google import genai
import sys

# ANSI Colors
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def test_key():
    print("--- 🔑 API Key Diagnostic ---")
    
    # 1. Get Key
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("❌ GEMINI_API_KEY env var is NOT set.")
        key = input("Please paste your key here to test: ").strip()
    else:
        print(f"✅ Found GEMINI_API_KEY in env: {key[:5]}...{key[-5:]}")

    if not key:
        print("❌ No key provided. Exiting.")
        return

    # 2. Configure Client
    print(f"\nAttempting to connect with key: '{key}' (Length: {len(key)})")
    try:
        client = genai.Client(api_key=key)
    except Exception as e:
        print(f"{RED}❌ Crash during Client init: {e}{RESET}")
        return

    # 3. Test Call
    print("Sending test request (model='gemini-2.0-flash')...")
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents='Reply "OK" if you hear me.'
        )
        print(f"\n{GREEN}✅ SUCCESS!{RESET}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"\n{RED}❌ FAILED.{RESET}")
        print(f"Error details: {e}")
        # Common errors help
        if "403" in str(e):
            print("\n💡 Hint: 403 usually means the key is invalid or the project does not have the Generative AI API enabled.")
        if "404" in str(e):
            print("\n💡 Hint: 404 indicates the model 'gemini-1.5-flash' might not be available for this key/region.")

if __name__ == "__main__":
    test_key()
