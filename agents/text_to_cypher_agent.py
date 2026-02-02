import json
import time
import os
from services.graph_service import graphdb
from services.gemini_graphrag import GeminiLLM

# ANSI Colors for CLI
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

class TextToCypherAgent:
    def __init__(self, api_key, debug_dir=None):
        # Requesting the high-end model first as per user request ("Gemini 3.0" intent)
        # Using newest available experimental pro model.
        self.llm = GeminiLLM(api_key=api_key, model_name="gemini-2.0-pro-exp-02-05") 
        self.schema = None
        self.schema_logged = False
        
        # Logging setup
        if debug_dir:
            self.debug_dir = debug_dir
        else:
            self.debug_dir = "debug"
            os.makedirs(self.debug_dir, exist_ok=True)
            
        # Rotation handled automatically by BaseAgent / Logging utils rotation rules
        # from core.logging_utils import rotate_logs
        # rotate_logs(self.debug_dir)
        
        # Standardize log file name
        self.debug_log_path = os.path.join(self.debug_dir, "debug_llm_TextToCypherAgent.md")
            
        # Initialize log if not exists (or recreated after rotation)
        if not os.path.exists(self.debug_log_path):
            with open(self.debug_log_path, "w") as f:
                f.write("# Text-to-Cypher Debug Log\n\n")

    def _log_conversation(self, user_input, cypher, results, error=None, model="Unknown"):
        """Logs the interaction to a file for triage."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Format results for logging
        result_str = "N/A"
        if results is not None:
            if isinstance(results, list):
                result_str = f"Count: {len(results)}\nSample: {json.dumps(results[:3], default=str)}"
            else:
                result_str = str(results)
        
        with open(self.debug_log_path, "a") as f:
             # Log Schema on first use
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
            # Fallback simple schema if APOC fails
            self.schema = {"note": "Schema extraction failed. Assume standard nodes like Person, Organization, etc."}
        
        # Validate schema size (simple check)
        schema_str = json.dumps(self.schema)
        if len(schema_str) > 100000:
            print(f"{YELLOW}⚠️ Schema is very large ({len(schema_str)} chars). Truncating for prompt...{RESET}")
            self.schema = str(self.schema)[:20000] + "... (truncated)"
        
        return self.schema

    def generate_query_with_retry(self, user_input, max_retries=2):
        """
        Generates Cypher from input, validates it, and retries if invalid.
        """
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
- **Ingredient Nodes**: Use the property `name` (e.g., "Cocoa") instead of `ingredient_name`, even if the schema lists both.
- **Ambiguity**: If a property seems duplicated (e.g. name vs ingredient_name), prefer `name`.

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
                response = self.llm.invoke(prompt, system_instruction=system_instruction)
                cypher = response.content.strip()
                
                # Check used model
                used_model = getattr(self.llm, "last_used_model", "Unknown")
                print(f"{CYAN}🤖 Model Used: {used_model}{RESET}")
                
                # Cleanup markdown code blocks if any remain
                cypher = cypher.replace("```cypher", "").replace("```", "").strip()
                
                if cypher == "N/A":
                    self._log_conversation(user_input, None, None, error="Returned N/A", model=used_model)
                    return None
                
                # Validate
                is_valid, error = graphdb.validate_cypher(cypher)
                
                if is_valid:
                    # Don't log success here yet, wait for execution result to log everything in one block? 
                    # Actually, we split logs: Generation vs Execution.
                    # But the user wants result logged when "LLM generated cypher is sent".
                    # I will log "Pending" here, and then update/append in execution.
                    # OR better: I will just hold logging until execution is done? 
                    # No, retry loop might fail.
                    # I'll log as "Pending Execution" here.
                    self._log_conversation(user_input, cypher, None, model=used_model) # Log Generated Cypher
                    return cypher
                else:
                    last_error = error
                    # Log failed attempt
                    self._log_conversation(user_input, cypher, None, error=f"Validation Failed: {error}", model=used_model)
                    
            except Exception as e:
                last_error = str(e)
                used_model = getattr(self.llm, "last_used_model", "Unknown")
                self._log_conversation(user_input, None, None, error=f"LLM Error: {e}", model=used_model)
            
            attempt += 1
            
        print(f"{RED}❌ Failed to generate valid Cypher after retries.{RESET}")
        return None

    def execute_query(self, cypher):
        print(f"\n{CYAN}Generated Cypher:{RESET}\n{cypher}")
        start = time.time()
        results = graphdb.send_query(cypher)
        duration = time.time() - start
        
        if isinstance(results, dict) and "status" in results and results["status"] == "error":
             print(f"{RED}Runtime Error: {results['message']}{RESET}")
             # Log runtime error
             with open(self.debug_log_path, "a") as f:
                 f.write(f"**Runtime Error:** {results['message']}\n\n---\n")
             return None
             
        print(f"{GREEN}✓ Executed in {duration:.2f}s{RESET}")
        
        # Log Execution Results
        try:
             result_str = f"Count: {len(results)}\nSample: {json.dumps(results[:5], default=str)}" if isinstance(results, list) else str(results)
             with open(self.debug_log_path, "a") as f:
                 f.write(f"**Execution Results:**\n```json\n{result_str}\n```\n\n---\n")
        except Exception as e:
            print(f"Log Error: {e}")
            
        return results

    def run_interactive_loop(self):
        print(f"\n{CYAN}--- 💬 Text-to-Cypher Interface ---{RESET}")
        print("Type your question below. Type 'exit' to return to menu.")
        
        # Pre-fetch schema
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
                        # Pretty print first few
                        print(json.dumps(results[:5], indent=2, default=str))
                        if len(results) > 5:
                            print(f"... and {len(results)-5} more.")
                    elif results is not None: # Empty list
                        print(f"{YELLOW}No results found.{RESET}")
                else:
                    print(f"{YELLOW}Could not understand valid query or request was N/A.{RESET}")
                    
            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}")
