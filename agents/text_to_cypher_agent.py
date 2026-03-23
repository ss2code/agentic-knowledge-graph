import json
import time
import os
from services.graph_service import graphdb
from agents.schema_agent import BaseAgent

# ANSI Colors for CLI
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


class TextToCypherAgent(BaseAgent):
    def __init__(self, api_key=None, debug_dir=None, model_name=None):
        if debug_dir is None:
            debug_dir = "debug"
            os.makedirs(debug_dir, exist_ok=True)

        super().__init__(model_name=model_name, debug_dir=debug_dir, module_name="TextToCypherAgent")

        self.schema = None
        self.schema_logged = False

        # Dedicated per-session conversation log (separate from LLM interaction log)
        self.debug_log_path = os.path.join(debug_dir, "debug_llm_TextToCypherAgent.md")
        if not os.path.exists(self.debug_log_path):
            with open(self.debug_log_path, "w") as f:
                f.write("# Text-to-Cypher Debug Log\n\n")

    def _log_conversation(self, user_input, cypher, results, error=None, model="Unknown"):
        """Logs the interaction to the conversation log file."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        result_str = "N/A"
        if results is not None:
            if isinstance(results, list):
                result_str = f"Count: {len(results)}\nSample: {json.dumps(results[:3], default=str)}"
            else:
                result_str = str(results)

        with open(self.debug_log_path, "a") as f:
            if not self.schema_logged and self.schema:
                f.write(f"## [{timestamp}] INITIAL SCHEMA CONTEXT\n")
                f.write("```json\n")
                f.write(json.dumps(self.schema, indent=2, default=str))
                f.write("\n```\n\n---\n\n")
                self.schema_logged = True

            f.write(f"## [{timestamp}] User Query\n")
            f.write(f"**Input:** `{user_input}`\n")
            f.write(f"**Model Used:** `{model}`\n\n")
            if cypher:
                f.write(f"**Generated Cypher:**\n```cypher\n{cypher}\n```\n")
            if error:
                f.write(f"**Error:** {error}\n")
            if results is not None:
                f.write(f"**Execution Results:**\n```json\n{result_str}\n```\n")
            f.write("\n---\n")

    def get_schema(self):
        """Fetches and caches schema."""
        print(f"{YELLOW}>> Fetching Schema (APOC)...{RESET}")
        self.schema = graphdb.get_schema_visualization()
        if not self.schema:
            print(f"{RED}⚠️ Could not extract schema. Agent might hallucinate structure.{RESET}")
            self.schema = {"note": "Schema extraction failed."}

        schema_str = json.dumps(self.schema)
        if len(schema_str) > 100000:
            print(f"{YELLOW}⚠️ Schema is very large ({len(schema_str)} chars). Truncating...{RESET}")
            self.schema = str(self.schema)[:20000] + "... (truncated)"

        return self.schema

    def generate_query_with_retry(self, user_input, max_retries=2):
        """Generates Cypher from input, validates it, retries on syntax error."""
        if not self.schema:
            self.get_schema()

        schema_text = json.dumps(self.schema, indent=2)

        system_instruction = f"""
### SYSTEM INSTRUCTIONS ###
You are an expert Neo4j Cypher developer converting natural language to Cypher queries.
Your goal is to answer questions about the graph data.

### SECURITY CONSTRAINTS ###
1. Generate READ-ONLY queries only. NEVER generate CREATE, DELETE, MERGE, or SET operations.
2. Always limit results to the top 20 unless specified otherwise (use LIMIT 20).
3. If the user asks a question unrelated to the schema, return "N/A".
4. Do not return markdown (e.g., ```cypher). Return ONLY the raw query string.

### DATA SCHEMA HINTS ###
- **Ingredient Nodes**: Use the property `name` (e.g., "Cocoa") instead of `ingredient_name`.
- **Ambiguity**: If a property seems duplicated, prefer `name`.

### DATA SCHEMA ###
{schema_text}

### FEW-SHOT EXAMPLES ###
User: "How many people are there?"
Cypher: MATCH (n:Person) RETURN count(n)

User: "Show me 5 organizations."
Cypher: MATCH (o:Organization) RETURN o.name LIMIT 5
"""

        prompt = f"### USER QUERY ###\n{user_input}"
        attempt = 0
        last_error = None

        while attempt <= max_retries:
            if attempt > 0:
                print(f"{YELLOW}🔄 Retry {attempt}/{max_retries} due to syntax error...{RESET}")
                prompt += f"\n\n### PREVIOUS ERROR ###\nThe previous query generated an error: {last_error}\nPlease fix the syntax."

            try:
                full_prompt = f"{system_instruction}\n\n{prompt}"
                cypher, used_model = self._generate(full_prompt, function_name="generate_query")
                cypher = cypher.strip().replace("```cypher", "").replace("```", "").strip()

                print(f"{CYAN}🤖 Model Used: {used_model}{RESET}")

                if cypher == "N/A":
                    self._log_conversation(user_input, None, None, error="Returned N/A", model=used_model)
                    return None

                is_valid, error = graphdb.validate_cypher(cypher)

                if is_valid:
                    self._log_conversation(user_input, cypher, None, model=used_model)
                    return cypher
                else:
                    last_error = error
                    self._log_conversation(user_input, cypher, None,
                                          error=f"Validation Failed: {error}", model=used_model)

            except Exception as e:
                last_error = str(e)
                self._log_conversation(user_input, None, None, error=f"LLM Error: {e}", model=self.model_name)

            attempt += 1

        print(f"{RED}❌ Failed to generate valid Cypher after retries.{RESET}")
        return None

    def execute_query(self, cypher):
        print(f"\n{CYAN}Generated Cypher:{RESET}\n{cypher}")
        start = time.time()
        results = graphdb.send_query(cypher)
        duration = time.time() - start

        if isinstance(results, dict) and results.get("status") == "error":
            print(f"{RED}Runtime Error: {results['message']}{RESET}")
            with open(self.debug_log_path, "a") as f:
                f.write(f"**Runtime Error:** {results['message']}\n\n---\n")
            return None

        print(f"{GREEN}✓ Executed in {duration:.2f}s{RESET}")

        try:
            result_str = json.dumps(results, indent=2, default=str) if isinstance(results, list) else str(results)
            with open(self.debug_log_path, "a") as f:
                f.write(f"**Execution Results:**\n```json\n{result_str}\n```\n\n---\n")
        except Exception as e:
            print(f"Log Error: {e}")

        return results

    def run_interactive_loop(self):
        print(f"\n{CYAN}--- 💬 Text-to-Cypher Interface ---{RESET}")
        print("Type your question below. Type 'exit' to return to menu.")

        if os.path.exists(self.debug_log_path):
            try:
                os.remove(self.debug_log_path)
                with open(self.debug_log_path, "w") as f:
                    f.write("# Text-to-Cypher Debug Log (Run Fresh)\n\n")
            except OSError as e:
                print(f"{YELLOW}Could not clear log file: {e}{RESET}")

        self.get_schema()

        while True:
            try:
                user_input = input(f"\n{CYAN}Ask Graph > {RESET}").strip()
                if user_input.lower() in ['exit', 'quit', 'back']:
                    break
                if not user_input:
                    continue

                print(f"{YELLOW}🤔 Thinking...{RESET}")
                cypher = self.generate_query_with_retry(user_input)

                if cypher:
                    results = self.execute_query(cypher)
                    if results:
                        print(f"\n{GREEN}Results ({len(results)}):{RESET}")
                        print(json.dumps(results, indent=2, default=str))
                    elif results is not None:
                        print(f"{YELLOW}No results found.{RESET}")
                else:
                    print(f"{YELLOW}Could not generate valid query.{RESET}")

            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}")
