import os
import json
import time
import random
from agents.schema_agent import BaseAgent

# Reuse colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

class NERAgent(BaseAgent):
    """
    Agent responsible for Named Entity Recognition (NER) discovery.
    Identifies entity types to be extracted from unstructured text.
    """
    def propose_entities(self, intent, file_summaries, construction_plan):
        """
        Proposes a list of Entity Types for extraction.

        Args:
            intent (dict): User intent object.
            file_summaries (dict): Data file context.
            construction_plan (dict): The structured schema (Schema Design output).

        Returns:
            tuple: (str json_response, str model_name)
        """
        print(f"{CYAN}🧠 [NER Agent] Analyzing text for entities...{RESET}")
        
        # Extract well-known types from Schema Design (Dictionary Format)
        well_known_types = []
        if isinstance(construction_plan, dict):
            for key, rule in construction_plan.items():
                if isinstance(rule, dict) and rule.get('construction_type') == 'node':
                    well_known_types.append(rule.get('label'))
        elif 'nodes' in construction_plan: # Fallback for old format
             well_known_types = [node['label'] for node in construction_plan.get('nodes', [])]
        
        prompt = f"""
        You are an expert Named Entity Recognition (NER) Architect.
        
        CONTEXT:
        1. User Intent: "{intent['intent']}" - {intent.get('description', '')}
        2. Well-Known Entity Types (from structured schema): {well_known_types}
        3. Unstructured Data Files (Header & Content Sample):
        {json.dumps(file_summaries, indent=2)}
        
        TASK:
        Analyze the file samples (especially text/markdown files) and propose a list of "Entity Types" that should be extracted.
        
        DESIGN RULES:
        1. **Reuse**: If a "Well-Known" type appears in the text (e.g. "{well_known_types[0] if well_known_types else 'Product'}"), reuse that label.
        2. **Discover**: Propose NEW entity types that are relevant to the User Intent (e.g., "Complaint", "Feature", "Location").
        3. **Abstract**: Propose TYPES (e.g., "Person"), not instances (e.g., "John").
        
        OUTPUT JSON:
        {{
            "entity_types": ["Product", "Review", "Complaint"],
            "reasoning": "Reuse Product. Added Review and Complaint for sentiment analysis."
        }}
        """
        response, model_name = self._generate(prompt, function_name="propose_entities")
        return self._clean_json(response), model_name

    def _clean_json(self, text):
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return text

class FactExtractionAgent(BaseAgent):
    """
    Agent responsible for defining relationships (facts) between entities in unstructured text.
    """
    def propose_facts(self, intent, file_summaries, approved_entities):
        """
        Proposes Fact Types (Triples) linking approved entities.

        Args:
            intent (dict): User intent.
            file_summaries (dict): Data file context.
            approved_entities (list): List of entities approved in the NER step.

        Returns:
            tuple: (str json_response, str model_name)
        """
        print(f"{CYAN}🔗 [Fact Agent] Defining relationships (triples)...{RESET}")
        
        prompt = f"""
        You are an expert Knowledge Graph Engineer.
        
        CONTEXT:
        1. User Intent: "{intent['intent']}"
        2. Approved Entity Types: {approved_entities}
        3. Data Samples:
        {json.dumps(file_summaries, indent=2)}
        
        TASK:
        Propose "Fact Types" (Relationships) to extract from the text, linking the Approved Entity Types.
        A Fact Type is a Triple: (Subject) -> [PREDICATE] -> (Object).
        
        DESIGN RULES:
        1. **Strict Constraints**: Subject and Object MUST be from the "Approved Entity Types" list.
        2. **Action-Oriented**: Predicates should be verbs or verb phrases (e.g., MENTIONS, HAS_ISSUE, WROTE).
        3. **Relevance**: Only propose facts relevant to the intent.
        
        OUTPUT JSON:
        {{
            "facts": [
                {{"subject": "Review", "predicate": "MENTIONS", "object": "Product"}},
                {{"subject": "Review", "predicate": "HAS_COMPLAINT", "object": "Complaint"}}
            ],
            "reasoning": "Linking reviews to products and specific complaints."
        }}
        """
        response, model_name = self._generate(prompt, function_name="propose_facts")
        return self._clean_json(response), model_name

    def _clean_json(self, text):
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return text

class ExtractionSchemaLoop:
    """
    Orchestrates the Extraction Logic Design process.
    Coordinates NER and Fact Extraction agents.
    """
    def __init__(self, verbose=True, api_key=None, data_dir='data'):
        """
        Initialize the Extraction Logic Loop.

        Args:
            verbose (bool): Console verbosity.
            api_key (str): Gemini API Key.
            data_dir (str): Base data directory.
        """
        # Reuse BaseAgent logic for key resolution
        self.api_key = api_key or BaseAgent()._get_api_key()
        
        self.debug_dir = os.path.join(data_dir, 'debug')
        self.ner_agent = NERAgent(api_key=self.api_key, debug_dir=self.debug_dir, module_name="NERAgent")
        self.fact_agent = FactExtractionAgent(api_key=self.api_key, debug_dir=self.debug_dir, module_name="FactExtractionAgent")
        
        self.verbose = verbose
        self.data_dir = data_dir

    def load_context(self):
        # Load Intent
        with open(os.path.join(self.data_dir, 'user_intent.json'), 'r') as f:
            intent = json.load(f)
            
        # Load Construction Plan (Schema Design)
        plan_path = os.path.join(self.data_dir, 'construction_plan.json')
        if not os.path.exists(plan_path):
            raise Exception("Schema Design (construction_plan.json) missing. Run Schema Design first.")
        with open(plan_path, 'r') as f:
            construction_plan = json.load(f)
            
        # Load Files (Same logic as SchemaRefinementLoop)
        approved_path = os.path.join(self.data_dir, 'approved_files.json')
        with open(approved_path, 'r') as f:
            files_list = json.load(f)['files']
        
        file_summaries = {}
        for safe_path in files_list:
            if not os.path.exists(safe_path): continue
            
            with open(safe_path, 'r') as f:
                header = f.readline().strip()
                
            # Improved sampling (random access)
            sample = self._get_representative_sample(safe_path)
            
            file_summaries[os.path.basename(safe_path)] = {
                "header": header,
                "sample_content": sample
            }
                
        return intent, file_summaries, construction_plan

    def _get_representative_sample(self, file_path: str, max_lines=50, small_file_limit=10240):
        """
        Reads a file. If small, returns full content.
        If large, returns first 10 lines + random sample of 'max_lines' from the rest.
        """
        try:
            size = os.path.getsize(file_path)
            if size < small_file_limit:
                 with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                     return f.read()[:3000] # Still cap at 3000 chars

            # Large file strategy
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            if len(lines) <= max_lines:
                return "".join(lines)
            
            # Take first 10 lines (header context)
            sample = lines[:10]
            # Take random sample from the rest
            rest = lines[10:]
            if rest:
                sample.extend(random.sample(rest, min(len(rest), max_lines)))
            
            return "".join(sample)[:3000] # Cap total length
        except Exception as e:
            print(f"{RED}Error reading sample from {os.path.basename(file_path)}: {e}{RESET}")
            return ""

    def run(self):
        print(f"\n{CYAN}--- ⛏️  Starting Extraction Logic Design ---{RESET}")
        
        # Notify about logging
        if os.path.exists(self.debug_dir):
            print(f"{CYAN}📝 Logging NER to: {os.path.join(self.debug_dir, 'debug_llm_NERAgent.md')}{RESET}")
            print(f"{CYAN}📝 Logging Facts to: {os.path.join(self.debug_dir, 'debug_llm_FactExtractionAgent.md')}{RESET}")
        
        try:
            intent, file_summaries, construction_plan = self.load_context()
        except Exception as e:
            print(f"{RED}Error loading context: {e}{RESET}")
            return False

        # --- STEP 1: NER (Entities) ---
        print(f"\n{YELLOW}Step 1: Discovering Entity Types...{RESET}")
        entities_approved = False
        approved_entities_list = []
        
        while not entities_approved:
            json_str, model = self.ner_agent.propose_entities(intent, file_summaries, construction_plan)
            try:
                proposal = json.loads(json_str)
                entities = proposal.get('entity_types', [])
                reasoning = proposal.get('reasoning', '')
                
                print(f"\n{GREEN}Proposed Entities ({model}):{RESET}")
                print(f"Entities: {entities}")
                print(f"Reasoning: {reasoning}")
                
                choice = input(f"\n{CYAN}[A]pprove / [R]etry: {RESET}").strip().upper()
                if choice == 'A':
                    approved_entities_list = entities
                    entities_approved = True
                else:
                    print(f"{YELLOW}Retrying...{RESET}")
            except Exception as e:
                print(f"{RED}Error parsing NER proposal: {e}{RESET}")
                # Simple retry logic without feedback loop for now to match strict design
                continue

        # --- STEP 2: Fact Extraction (Relationships) ---
        print(f"\n{YELLOW}Step 2: Defining Facts (Relationships)...{RESET}")
        facts_approved = False
        final_extraction_plan = {}
        
        while not facts_approved:
            json_str, model = self.fact_agent.propose_facts(intent, file_summaries, approved_entities_list)
            try:
                proposal = json.loads(json_str)
                facts = proposal.get('facts', [])
                reasoning = proposal.get('reasoning', '')
                
                print(f"\n{GREEN}Proposed Facts ({model}):{RESET}")
                for fact in facts:
                    print(f"  - ({fact['subject']}) -> [{fact['predicate']}] -> ({fact['object']})")
                print(f"Reasoning: {reasoning}")
                
                choice = input(f"\n{CYAN}[A]pprove / [R]etry: {RESET}").strip().upper()
                if choice == 'A':
                    final_extraction_plan = {
                        "entities": approved_entities_list,
                        "facts": facts,
                        "model_used": model
                    }
                    facts_approved = True
                else:
                    print(f"{YELLOW}Retrying...{RESET}")
            except Exception as e:
                print(f"{RED}Error parsing Fact proposal: {e}{RESET}")
                continue

        # --- Save Result ---
        out_path = os.path.join(self.data_dir, 'extraction_plan.json')
        with open(out_path, 'w') as f:
            json.dump(final_extraction_plan, f, indent=2)
            
        print(f"\n{GREEN}✅ Extraction Plan Saved to {out_path}{RESET}")
        return True
