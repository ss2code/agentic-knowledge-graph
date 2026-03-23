import os
import json
import sys
import re

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.schema_agent import BaseAgent

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


class IntentAgent(BaseAgent):
    """
    Agent responsible for clarifying and defining the user's business intent.
    Inherits LLM calls and logging from BaseAgent (AnthropicProvider).
    """

    def __init__(self, data_dir='data', model_name=None):
        self.data_dir = data_dir
        debug_dir = os.path.join(data_dir, 'debug')
        super().__init__(model_name=model_name, debug_dir=debug_dir, module_name="IntentAgent")
        if self.provider:
            print(f"{GREEN}✅ Anthropic API configured successfully.{RESET}")

    # ------------------------------------------------------------------
    # Core LLM method
    # ------------------------------------------------------------------

    def refine_intent(self, user_input):
        """
        Refines raw user input into a structured intent JSON using the LLM.

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

        full_prompt = f"{system_prompt}\nUser Input: {user_input}"

        if self.provider:
            try:
                text, _model = self._generate(full_prompt, function_name="refine_intent")
                text = text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                if text.startswith("{") and text.endswith("}"):
                    return True, text
                else:
                    return False, text
            except Exception as e:
                return False, f"Error calling LLM: {e}"
        else:
            # Simulation mode heuristics
            match = re.search(r"trace\s+(.*?)\s+to\s+(.*)", user_input, re.IGNORECASE)
            if match:
                source, target = match.groups()
                source = source.strip().title()
                target = target.strip().rstrip('.').title()
                simulated = json.dumps({
                    "intent": f"Trace {source} to {target}",
                    "description": f"Map {source} to {target} to identify relationships.",
                    "primary_entities": [source, target],
                    "reasoning": "Detected explicit traversal request."
                }, indent=2)
                is_valid = True
            else:
                match_analyze = re.search(r"analyze\s+(.*)", user_input, re.IGNORECASE)
                if match_analyze:
                    topic = match_analyze.group(1).strip().rstrip('.').title()
                    if len(topic.split()) < 5:
                        simulated = json.dumps({
                            "intent": f"Analyze {topic}",
                            "description": f"Investigate relationships within {topic}.",
                            "primary_entities": [topic, "Context"],
                            "reasoning": "User requested focus on a specific domain topic."
                        }, indent=2)
                        is_valid = True
                    else:
                        simulated = (
                            "Guidance: That is a bit vague. I need to know what you want to connect.\n"
                            "Try: 'I want to trace [Source] to [Target]'."
                        )
                        is_valid = False
                else:
                    simulated = (
                        "Guidance: That is a bit vague. I need to know what you want to connect.\n"
                        "Try: 'I want to trace [Source] to [Target]'."
                    )
                    is_valid = False

            if self.log_file:
                from core.logging_utils import log_llm_interaction
                log_llm_interaction(
                    self.log_file, self.module_name, "simulation-model",
                    "refine_intent", full_prompt, simulated
                )
            return is_valid, simulated

    def refine_intent_from_text(self, goal: str) -> dict:
        """
        Calls LLM, saves user_intent.json, returns refined intent dict.
        Raises ValueError if LLM rejects the goal.
        """
        is_valid, response_text = self.refine_intent(goal)
        if is_valid:
            intent_dict = json.loads(response_text)
            self.save_intent(response_text)
            return intent_dict
        else:
            raise ValueError(response_text)

    def save_intent(self, intent_json):
        """Saves the final intent to user_intent.json."""
        os.makedirs(self.data_dir, exist_ok=True)
        path = os.path.join(self.data_dir, 'user_intent.json')
        with open(path, 'w') as f:
            f.write(intent_json)
        print(f"\n{GREEN}✅ Intent saved to {os.path.abspath(path)}{RESET}")

    def run_interactive_session(self):
        print(f"\n{CYAN}--- 🤖 IntentAgent ---{RESET}")
        print("I am here to help you define the 'North Star' of your Knowledge Graph.")

        existing_intent = None
        path = os.path.join(self.data_dir, 'user_intent.json')
        if os.path.exists(path):
            try:
                with open(path) as f:
                    existing_intent = json.load(f).get('intent')
            except Exception:
                pass

        if existing_intent:
            print(f"\n{YELLOW}📜 Existing Intent: \"{existing_intent}\"{RESET}")
            print("Press [Enter] to keep it, or type a new goal.")
            default_suggestion = existing_intent
        else:
            print("Tell me about your dataset and business goal.")
            print('Example: "I want to trace customer complaints to ingredients."')
            default_suggestion = "I want to trace customer complaints to ingredients."

        try:
            user_input = input(f"\n{CYAN}Your Goal (Default: {default_suggestion}): {RESET}").strip()
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Cancelled.{RESET}")
            sys.exit(0)

        if not user_input:
            user_input = default_suggestion

        print(f"\n🔄 Analysing: \"{user_input}\"...")

        while True:
            is_valid, response = self.refine_intent(user_input)

            if is_valid:
                print(f"\n{GREEN}✅ Intent configuration:{RESET}")
                print(response)
                try:
                    confirm = input(f"\n{CYAN}Lock this intent? (y/n): {RESET}").strip().lower()
                except KeyboardInterrupt:
                    sys.exit(0)

                if confirm == 'y':
                    self.save_intent(response)
                    break
                else:
                    user_input = input(f"\n{YELLOW}Please rephrase your goal: {RESET}").strip()
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
