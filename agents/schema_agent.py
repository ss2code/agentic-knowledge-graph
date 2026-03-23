import os
import json
import time
from services.llm_provider import AnthropicProvider

# Reuse colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

class BaseAgent:
    """
    Base class for all agents. Uses AnthropicProvider for LLM calls.
    Falls back to simulation mode when PROJECT_ANTHROPIC_API_KEY is not set.
    """
    def __init__(self, model_name=None, debug_dir=None, module_name="BaseAgent",
                 # Legacy params kept for call-site compatibility during migration
                 api_key=None):
        self.module_name = module_name
        self.model_name = model_name or AnthropicProvider.DEFAULT_MODEL
        self.debug_dir = debug_dir
        self.log_file = None

        if self.debug_dir:
            from core.logging_utils import get_log_file_path
            self.log_file = get_log_file_path(self.debug_dir, self.module_name)

        try:
            self.provider = AnthropicProvider()
        except ValueError:
            print(f"{YELLOW}⚠️  PROJECT_ANTHROPIC_API_KEY not set. Running in SIMULATION MODE.{RESET}")
            self.provider = None

    def _generate(self, prompt, function_name="Unknown"):
        """
        Generate content via AnthropicProvider.

        Returns:
            tuple: (str response_text, str model_used)
        """
        if self.provider is None:
            simulated = json.dumps({
                "nodes": [],
                "relationships": [],
                "reasoning": "SIMULATION MODE: No API key provided."
            })
            if self.log_file:
                from core.logging_utils import log_llm_interaction
                log_llm_interaction(
                    self.log_file, self.module_name, "simulation-model",
                    function_name, prompt, simulated
                )
            return simulated, "simulation-model"

        text, model_used = self.provider.generate(prompt, model=self.model_name, log_file=self.log_file)
        if self.log_file:
            from core.logging_utils import log_llm_interaction
            log_llm_interaction(
                self.log_file, self.module_name, model_used,
                function_name, prompt, text
            )
        return text, model_used

class SchemaProposalAgent(BaseAgent):
    """
    Agent responsible for proposing the initial Neo4j schema based on intent and data samples.
    """
    def propose_schema(self, intent, file_summaries, feedback=None):
        """
        Generates a draft schema (Construction Plan).

        Args:
            intent (dict): User intent object.
            file_summaries (dict): Headers and sample rows of data files.
            feedback (str, optional): Feedback from a previous Critic iteration.

        Returns:
            tuple: (str schema_json, str model_used)
        """
        print(f"{CYAN}🤖 [Architect] drafting schema...{RESET}")
        
        prompt = f"""
        You are a Neo4j Graph Architect. 
        User Intent: "{intent['intent']}" - {intent['description']}
        Primary Entities: {intent['primary_entities']}
        
        Data Files available:
        {json.dumps(file_summaries, indent=2)}
        
        TASK: Create a Schema / Construction Plan.
        - Map files to Node Labels.
        - Map columns to Properties.
        - Define Relationships between nodes.
        - Important: If a column contains multiple values (e.g. "Flour, Sugar"), suggest a transformation to split it.
        
        CONSTRAINTS:
        1. Output ONLY valid JSON. No conversational text or markdown text outside the code block.
        2. Node Labels MUST be strict PascalCase with NO spaces (e.g., "ProductCategory", not "Product Category").
        3. Relationship Types MUST be SCREAMING_SNAKE_CASE (e.g., "BELONGS_TO").
        
        {f"PREVIOUS FEEDBACK TO ADDRESS: {feedback}" if feedback else ""}
        
        OUTPUT JSON format (Dictionary of Rules):
        {{
          "Product": {{
            "construction_type": "node",
            "source_file": "products.csv",
            "label": "Product",
            "unique_column_name": "id",
            "properties": ["id", "name", "price"]
          }},
          "ABOUT_PRODUCT": {{
            "construction_type": "relationship",
            "source_file": "products.csv",
            "relationship_type": "ABOUT_PRODUCT",
            "from_node_label": "CustomerReview",
            "from_node_column": "extracted_product_name",
            "to_node_label": "Product",
            "to_node_column": "name",
            "rule": "Use NLP to extract product names from Review text, then match against Product.name"
          }},
          "reasoning": "Explanation of design choices"
        }}
        }}
        """
        response, model_used = self._generate(prompt, function_name="propose_schema")
        return self._clean_json(response), model_used

    def _clean_json(self, text):
        import re
        text = text.strip()
        # Try to find JSON block
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: Find first { and last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
            
        return text

class SchemaCriticAgent(BaseAgent):
    """
    Agent responsible for critiquing and validating proposed schemas against best practices.
    """
    def critique_schema(self, intent, schema_json, file_summaries):
        """
        Reviews a proposed schema.

        Args:
            intent (dict): User intent.
            schema_json (str): Proposed schema JSON string.
            file_summaries (dict): Data file context.

        Returns:
            tuple: (str critique_json, str model_used)
        """
        print(f"{YELLOW}🧐 [Critic] reviewing schema...{RESET}")
        
        prompt = f"""
        You are a strict Graph Schema Reviewer.
        
        CONTEXT:
        1. User Intent: "{intent['intent']}"
        2. Data Files available (Header & Sample):
        {json.dumps(file_summaries, indent=2)}
        
        Proposed Schema:
        {schema_json}
        
        KNOWLEDGE GRAPH BEST PRACTICES CHECKLIST:
        1. **Standardization**: Are Node Labels PascalCase (e.g., 'Product') and Relationships SCREAMING_SNAKE_CASE (e.g., 'HAS_INGREDIENT')?
        2. **Atomicity**: logical check - if a sample row has "A, B, C", is there a rule to split it?
        3. **Consistency**: Do the mapped properties match the actual file headers provided above?
        4. **Simplicity**: No redundant nodes.
        
        VERIFY:
        1. Does specific `unique_column_name` exist in the file header? (skip for unstructured .txt)
        2. Are relationship mappings accurate? 
           - **EXCEPTION**: If the rule involves "NLP", "LLM", or "Extraction", you MUST allow the `from_node_column` or `to_node_column` to be a "derived" field (like 'extracted_product_name') even if it's not in the file header.
        3. Are all construction types 'node' or 'relationship'?
        4. **CRITICAL**: Do any labels contain spaces? If so, REJECT immediately.
        
        OUTPUT JSON:
        {{
           "status": "VALID" or "RETRY",
           "feedback": "If RETRY, explain strictly what is wrong using the checklist. If VALID, say 'Looks good'."
        }}
        }}
        """
        response, model_used = self._generate(prompt, function_name="critique_schema")
        return self._clean_json(response), model_used

    def _clean_json(self, text):
        import re
        text = text.strip()
        # Try to find JSON block
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
            
        # Fallback: Find first { and last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
            
        return text

class SchemaRefinementLoop:
    """
    Orchestrates the negotiation loop between the Proposer and Critic agents.
    """
    def __init__(self, verbose=True, api_key=None, data_dir='data', model_name=None):
        self.debug_dir = os.path.join(data_dir, 'debug')
        self.proposer = SchemaProposalAgent(model_name=model_name, debug_dir=self.debug_dir, module_name="SchemaRefinement")
        self.critic = SchemaCriticAgent(model_name=model_name, debug_dir=self.debug_dir, module_name="SchemaRefinement")
        
        self.verbose = verbose
        self.data_dir = data_dir

    def load_context(self):
        # Load Intent
        intent_path = os.path.join(self.data_dir, 'user_intent.json')
        with open(intent_path, 'r') as f:
            intent = json.load(f)
        
        # Load Files
        approved_path = os.path.join(self.data_dir, 'approved_files.json')
        if not os.path.exists(approved_path):
            raise Exception(f"No approved files found at {approved_path}. Run Phase 3a first.")
            
        with open(approved_path, 'r') as f:
            files_list = json.load(f)['files']
        
        file_summaries = {}
        for safe_path in files_list:
            if not os.path.exists(safe_path): continue
            with open(safe_path, 'r') as f:
                header = f.readline().strip()
                sample = f.readline().strip()
                file_summaries[os.path.basename(safe_path)] = {
                    "header": header,
                    "sample_row": sample
                }
        return intent, file_summaries

    def run(self):
        print(f"\n{CYAN}--- 🔄 Starting Schema Negotiation Loop (Verbose={self.verbose}) ---{RESET}")
        
        # Notify about logging
        if os.path.exists(self.debug_dir):
            print(f"{CYAN}📝 Logging Schema Refinement to: {os.path.join(self.debug_dir, 'debug_llm_SchemaRefinement.md')}{RESET}")
        
        try:
            intent, file_summaries = self.load_context()
        except Exception as e:
            print(f"{RED}Context Load Error: {e}{RESET}")
            return False
            
        feedback = None
        max_retries = 3
        
        success = False
        
        for i in range(max_retries):
            print(f"\n{CYAN}--- Iteration {i+1}/{max_retries} ---{RESET}")
            
            # 1. Propose
            schema_str, proposer_model = self.proposer.propose_schema(intent, file_summaries, feedback)
            
            if self.verbose:
                print(f"[DEBUG] Raw Proposal Length: {len(schema_str)} (Model: {proposer_model})")
            
            try:
                # Validate JSON syntax
                json_obj = json.loads(schema_str)
                # Pretty print if verbose
                if self.verbose:
                     print(f"{CYAN}Draft Schema:{RESET}")
                     print(json.dumps(json_obj, indent=2))
                else:
                     print(f"{GREEN}Draft Generated.{RESET}")
            except json.JSONDecodeError as e:
                print(f"{RED}Proposer generated invalid JSON.{RESET}")
                
                if self.verbose:
                    print(f"{RED}--- RAW OUTPUT START ---{RESET}")
                    print(schema_str)
                    print(f"{RED}--- RAW OUTPUT END ---{RESET}")
                    print(f"Error: {e}")
                
                # Feedback for next loop (self-correction)
                feedback = f"Your previous output was NOT valid JSON. Error: {e}. Output ONLY JSON."
                continue

            # 2. Critique
            critique_str, critic_model = self.critic.critique_schema(intent, schema_str, file_summaries)
            
            try:
                critique = json.loads(critique_str)
            except json.JSONDecodeError as e:
                print(f"{RED}Critic generated invalid JSON. Skipping iteration.{RESET}")
                if self.verbose:
                    print(f"Raw Critique: {critique_str}")
                continue
            
            print(f"Critic Verdict: {critique.get('status')}")
            if self.verbose or critique.get('status') != "VALID":
                print(f"Feedback: {critique.get('feedback')}")
            
            if critique.get('status') == "VALID":
                print(f"\n{GREEN}✅ Consensus Reached!{RESET}")
                out_path = os.path.join(self.data_dir, 'construction_plan.json')
                with open(out_path, 'w') as f:
                    f.write(schema_str)
                success = True
                break
            else:
                feedback = critique.get('feedback')
                print(f"{YELLOW}Revising based on feedback...{RESET}")
                time.sleep(1)
        
        if not success:
            print(f"\n{RED}❌ Max iterations reached without consensus.{RESET}")

        return success
