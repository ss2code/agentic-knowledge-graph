import os
import json
import sys
import getpass
import re
import time
import random
from google import genai

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

class IntentAgent:
    """
    Agent responsible for clarifying and defining the user's business intent for the Knowledge Graph.
    Uses LLMs to refine vague requests into structured goals.
    """
    def __init__(self, data_dir='data'):
        """
        Initialize the Intent Agent.

        Args:
            data_dir (str): Base directory for data storage. Defaults to 'data'.
        """
        self.data_dir = data_dir
        self.debug_dir = os.path.join(data_dir, 'debug')
        self.api_key = self._get_valid_api_key()
        
        from core.logging_utils import get_log_file_path
        self.log_file = get_log_file_path(self.debug_dir, "IntentAgent")
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print(f"{GREEN}✅ Gemini API configured successfully.{RESET}")
            except Exception as e:
                 print(f"{YELLOW}⚠️ Error configuring Gemini: {e}. Running in SIMULATION MODE.{RESET}")
                 self.client = None
        else:
            print(f"{YELLOW}⚠️ No verified API key. Running in SIMULATION MODE.{RESET}")
            self.client = None

    def _get_valid_api_key(self):
        """
        Retrieves and validates the Gemini API key.
        Checks environment variables first, then prompts the user.
        
        Returns:
            str: Valid API Key, or None if validation fails.
        """
        # 1. Check Environment
        key = os.getenv("GEMINI_API_KEY")
        if key:
            print(f"{CYAN}Found GEMINI_API_KEY in environment.{RESET}")
            if self._validate_key(key):
                return key
            else:
                print(f"{RED}Environment key failed validation.{RESET}")
        
        # 2. Prompt User
        print(f"\n{CYAN}No valid API key found.{RESET}")
        print(f"You can get one from: https://aistudio.google.com/app/apikey")
        print(f"Press [Enter] to skip and use Simulation Mode.")
        
        # We use input() instead of getpass() so the user can verify their paste worked.
        try:
            key = input(f"{CYAN}Enter Gemini API Key (visible): {RESET}").strip()
        except Exception:
            # Fallback
            key = ""

        if not key:
            return None

        # 3. Validate
        print(f"Validating key...")
        if self._validate_key(key):
            return key
        else:
            print(f"{RED}Key validation failed.{RESET}")
            return None

    def _validate_key(self, key):
        """Lightweight validation using multiple models."""
        # Because we don't have self.client yet (we are validating the key to CREATE it),
        # we must create a temporary client.
        try:
             temp_client = genai.Client(api_key=key)
             # Try the fallback list manually or just a couple of likely ones
             candidates = ['gemini-2.0-flash-exp', 'gemini-flash-latest']
             for model in candidates:
                 try:
                     temp_client.models.generate_content(
                        model=model, 
                        contents='Hi'
                    )
                     return True
                 except:
                     continue
             return False
        except:
             return False

    def _generate_with_fallback(self, prompt, function_name="Unknown"):
        """
        Attempts to generate content using a prioritized list of models.
        Implements exponential backoff for rate limits (429).
        
        Args:
            prompt (str): The input prompt for the LLM.
            function_name (str): Calling function name for logging purposes.
            
        Returns:
            GenerateContentResponse: The LLM response object.
            
        Raises:
            Exception: If all models fail.
        """
        # Prioritized list based on 'what worked' in other projects + list_models output
        model_candidates = [
            'gemini-2.0-flash-exp', 
            'gemini-2.0-flash', 
            'gemini-2.0-flash-lite-preview-02-05',
            'gemini-flash-latest'
        ]
        
        errors = []

        for model_name in model_candidates:
            # Simple retry for 429
            for attempt in range(3):
                try:
                    # print(f"DEBUG: Trying {model_name} (Attempt {attempt+1})...")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    
                    if self.log_file:
                        from core.logging_utils import log_llm_interaction
                        log_llm_interaction(self.log_file, "IntentAgent", model_name, function_name, prompt, response.text)

                    return response
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                        # Exponential backoff
                        sleep_time = (2 ** attempt) + (random.random() * 0.5)
                        # print(f"DEBUG: 429 Hit. Sleeping {sleep_time:.2f}s...")
                        time.sleep(sleep_time)
                        continue
                    elif "404" in error_str or "not found" in error_str.lower():
                        # Model not available, skip to next candidate immediately
                        break
                    else:
                        # Other error, log and try next candidate
                        errors.append(f"{model_name}: {error_str}")
                        break
        
        # If we get here, everything failed
        raise Exception(f"All models failed. Errors: {errors}")

    def refine_intent(self, user_input):
        """
        Refines raw user input into a structured intent configuration using the LLM.

        Args:
            user_input (str): The raw goal description from the user.

        Returns:
            tuple: (bool is_valid, str response_text)
        """
        system_prompt = """
        You are an expert Data Architect.
        Your goal is to extract a clear, actionable business goal for a Knowledge Graph from the user's input,
        WITHOUT assuming any specific domain (e.g., it could be Finance, Biology, Supply Chain, etc.).
        
        Rules:
        1. REJECT vague goals like "analyze data" or "find insights". Ask for specifics.
        2. ACCEPT specific goals where the user mentions connecting concepts (e.g., "Trace X to Y").
        3. OUTPUT FORMAT:
           - If REJECTING: Plain text critique.
           - If ACCEPTING: A JSON object (and ONLY JSON) with:
             {
               "intent": "Short Title",
               "description": "One sentence summary",
               "primary_entities": ["List", "Of", "Node", "Labels"],
               "reasoning": "Why this is a good graph use case"
             }
        """
        
        if self.client:
            try:
                # Use the new fallback method
                response = self._generate_with_fallback(f"{system_prompt}\nUser Input: {user_input}", function_name="refine_intent")
                
                text = response.text.strip()
                if text.startswith("```json"): text = text[7:]
                if text.endswith("```"): text = text[:-3]
                text = text.strip()

                if text.startswith("{") and text.endswith("}"):
                    return True, text
                else:
                    return False, text
            except Exception as e:
                 return False, f"Error calling LLM: {e}"
        else:
            # Generic Simulation Logic
            # Heuristic: Look for "Trace X to Y" or "Link A and B" pattern
            match = re.search(r"trace\s+(.*?)\s+to\s+(.*)", user_input, re.IGNORECASE)
            if match:
                source, target = match.groups()
                # Clean up punctuation
                source = source.strip().title()
                target = target.strip().rstrip('.').title()
                return True, json.dumps({
                    "intent": f"Trace {source} to {target}",
                    "description": f"Map {source} to {target} to identify relationships.",
                    "primary_entities": [source, target],
                    "reasoning": "Detected explicit traversal request."
                }, indent=2)
            
            # Heuristic: "Analyze [Topic]"
            match_analyze = re.search(r"analyze\s+(.*)", user_input, re.IGNORECASE)
            if match_analyze:
                 topic = match_analyze.group(1).strip().rstrip('.').title()
                 if len(topic.split()) < 5: # If it's short enough to be a topic
                    return True, json.dumps({
                        "intent": f"Analyze {topic}",
                        "description": f"Investigate relationships within {topic}.",
                        "primary_entities": [topic, "Context"],
                        "reasoning": "User requested focus on a specific domain topic."
                    }, indent=2)

            return False, f"Guidance: That is a bit vague. I need to know what you want to connect. \nTry: 'I want to trace [Source] to [Target]'."

    def save_intent(self, intent_json):
        """Saves the final intent to a file, acting as a contract for Phase 3."""
        os.makedirs(self.data_dir, exist_ok=True)
        path = os.path.join(self.data_dir, 'user_intent.json')
        with open(path, 'w') as f:
            f.write(intent_json)
        abs_path = os.path.abspath(path)
        print(f"\n{GREEN}✅ Intent 'Contract' saved to {abs_path}{RESET}")

    def run_interactive_session(self):
        print(f"\n{CYAN}--- 🤖 Professor Graph's IntentAgent (Generic) ---{RESET}")
        print("I am here to help you define the 'North Star' of your Knowledge Graph.")
        
        # Load existing if available
        existing_intent = None
        path = os.path.join(self.data_dir, 'user_intent.json')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    existing_intent = data.get('intent')
            except:
                pass
        
        if existing_intent:
             print(f"\n{YELLOW}📜 Existing Intent Found: \"{existing_intent}\"{RESET}")
             print("Do you want to keep this? (Press [Enter]) Or type a new goal?")
             default_suggestion = existing_intent
        else:
             print("Tell me about your dataset and business goal.")
             print(f"Example: \"I want to trace customer complaints to ingredients.\"")
             default_suggestion = "I want to trace customer complaints to ingredients."
             
        try:
            user_input = input(f"\n{CYAN}Your Goal (Default: {default_suggestion}): {RESET}").strip()
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Class dismissed.{RESET}")
            sys.exit(0)
            
        if not user_input:
             user_input = default_suggestion

        print(f"\n🔄 Analyzing: \"{user_input}\"...")
        
        while True:
            is_valid, response = self.refine_intent(user_input)
            
            if is_valid:
                print(f"\n{GREEN}✅ I have distilled your intent into this configuration:{RESET}")
                print(response)
                try:
                    confirm = input(f"\n{CYAN}Do you want to lock this intent? (y/n): {RESET}").strip().lower()
                except KeyboardInterrupt:
                    sys.exit(0)

                if confirm == 'y':
                    self.save_intent(response)
                    break
                else:
                    user_input = input(f"\n{YELLOW}Okay, please rephrase your goal: {RESET}").strip()
            else:
                print(f"\n{RED}❌ Critique: {response}{RESET}")
                try:
                    user_input = input(f"\n{CYAN}Please try again (be specific): {RESET}").strip()
                except KeyboardInterrupt:
                    sys.exit(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data")
    args = parser.parse_args()
    
    agent = IntentAgent(data_dir=args.data_dir)
    agent.run_interactive_session()
