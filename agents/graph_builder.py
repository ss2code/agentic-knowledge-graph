import json
import os
import time
from services.graph_service import graphdb, CYAN, GREEN, YELLOW, RED, RESET
from agents.schema_agent import BaseAgent

class GraphBuilderAgent(BaseAgent):
    """
    Agent responsible for importing structured data (from CSV/JSON) into Neo4j
    based on the Construction Plan.
    Now supports Interactive Mode (Heuristic vs LLM).
    """
    def __init__(self, api_key=None, verbose=True, context=None):
        """
        Initialize the Graph Builder.
        """
        super().__init__(api_key=api_key, module_name="GraphBuilderAgent") 
        self.verbose = verbose
        self.context = context
        self.data_dir = context.data_dir if context else 'data'
        self.base_dir = context.base_path if context else 'data'
        
        # Use new logging utils via BaseAgent but ensure we point to the right place if needed
        if self.context:
             self.debug_dir = self.context.debug_dir
             # Re-init log file with correct path if BaseAgent didn't get debug_dir
             from core.logging_utils import get_log_file_path
             self.log_file = get_log_file_path(self.debug_dir, self.module_name)
             self.log_path = self.log_file # Alias for compatibility
        else:
             self.log_path = os.path.join('data', 'debug', 'graph_build_log.md')

    def log_step(self, step_name, details, status="INFO"):
        """Logs a step to the markdown file with a timestamp."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        icon = "✅" if status == "SUCCESS" else ("❌" if status == "ERROR" else "ℹ️")
        
        entry = f"\n### {icon} {step_name} ({timestamp})\n```text\n{details}\n```\n"
        
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, 'a') as f:
            f.write(entry)
            
        if self.verbose:
            color = GREEN if status == "SUCCESS" else (RED if status == "ERROR" else CYAN)
            print(f"{color}[{step_name}] {status}{RESET}")

    def load_construction_plan(self):
        path = os.path.join(self.base_dir, 'construction_plan.json')
        if not os.path.exists(path):
            path = os.path.join(self.data_dir, 'construction_plan.json')
            
        if not os.path.exists(path):
            raise Exception(f"construction_plan.json not found at {path}")
            
        with open(path, 'r') as f:
            return json.load(f)

    def create_constraints(self, nodes):
        self.log_step("Constraint Creation", "Starting uniqueness constraints checks...")
        for node in nodes:
            label = node['label']
            unique_id = node.get('unique_column_name', node.get('unique_id', 'id'))
            query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{unique_id} IS UNIQUE"
            result = graphdb.send_query(query)
            status = "ERROR" if isinstance(result, dict) and "error" in result else "SUCCESS"
            self.log_step(f"Constraint for {label}", f"Property: {unique_id}\nQuery: {query}", status)

    def _get_heuristic_node_query(self, node, filename):
        label = node['label']
        unique_id = node.get('unique_column_name', node.get('unique_id', 'id'))
        props = node.get('properties', [])
        rule = node.get('transformation_rule', '')
        
        if "split" in rule.lower() and "ingredients" in rule.lower():
            source_col = "ingredients" 
            return f"""
            LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
            UNWIND split(row['{source_col}'], ',') AS item
            WITH trim(item) as cleaned_item
            WHERE cleaned_item IS NOT NULL AND cleaned_item <> ''
            MERGE (n:{label} {{ {unique_id}: cleaned_item }})
            """
        elif filename.endswith('.txt'):
            text_prop = next((p for p in props if 'text' in p or 'content' in p), 'text')
            return f"""
            LOAD CSV FROM 'file:///{filename}' AS line
            WITH line, linenumber() AS ln
            WHERE line[0] IS NOT NULL
            MERGE (n:{label} {{ {unique_id}: toString(ln) }})
            SET n.{text_prop} = line[0]
            """
        else:
            base = f"""
            LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
            MERGE (n:{label} {{ {unique_id}: row['{unique_id}'] }})
            """
            set_parts = [f"n.{p} = row['{p}']" for p in props if p != unique_id]
            if set_parts: base += f"\nSET {', '.join(set_parts)}"
            return base

    def _generate_llm_query(self, task_desc, context_json):
        print(f"{CYAN}🤖 Generating Cypher via LLM...{RESET}")
        prompt = f"""
        You are a Neo4j Cypher Expert.
        
        TASK: Write a Cypher usage to `{task_desc}`.
        
        CONTEXT:
        {json.dumps(context_json, indent=2)}
        
        REQUIREMENTS:
        1. Return ONLY the Cypher Code block. No markdown wrapper needed if possible, or use ```cypher.
        2. Use `LOAD CSV WITH HEADERS FROM 'file:///...'`
        3. Handle nulls using `coalesce` or `WHERE` clauses if needed.
        4. Use `MERGE` to avoid duplicates.
        """
        response, _ = self._generate(prompt, function_name="generate_cypher")
        
        # Clean response
        if "```" in response:
            import re
            match = re.search(r"```(?:cypher)?\s*(.*?)\s*```", response, re.DOTALL)
            if match: return match.group(1)
        return response.strip()

    def import_nodes(self, nodes):
        self.log_step("Node Import", "Starting node batch import...")
        
        for node in nodes:
            label = node['label']
            source_file = node.get('source_file')
            if not source_file: continue
            filename = os.path.basename(source_file)
            
            # 1. Heuristic
            hq = self._get_heuristic_node_query(node, filename)
            
            print(f"\n{YELLOW}Node: {label} (File: {filename}){RESET}")
            choice = input(f"{CYAN}Import Strategy? [H]euristic (Default) / [L]LM / [C]ompare: {RESET}").strip().upper()
            
            final_query = hq
            
            if choice == 'L' or choice == 'C':
                lq = self._generate_llm_query(f"Import Nodes with Label {label}", node)
                if choice == 'L':
                    final_query = lq
                else:
                    print(f"\n{CYAN}--- Heuristic ---{RESET}\n{hq}")
                    print(f"\n{CYAN}--- LLM Generated ---{RESET}\n{lq}")
                    sel = input(f"\n{YELLOW}Select [H]euristic or [L]LM: {RESET}").strip().upper()
                    final_query = lq if sel == 'L' else hq

            self._execute_import(f"Import {label}", final_query)

    def import_relationships(self, nodes, relationships):
        self.log_step("Relationship Import", "Starting relationship import...")
        node_map = {n['label']: n for n in nodes}
        
        for rel in relationships:
            rel_type = rel.get('relationship_type', rel.get('type'))
            print(f"\n{YELLOW}Relationship: {rel_type}{RESET}")
            
            # Logic to find source file... (simplified for brevity, assume extraction from rel or source node)
            source_label = rel.get('from_node_label')
            source_file = rel.get('source_file')
            if not source_file:
                 source_file = node_map.get(source_label, {}).get('source_file')
            if not source_file: continue
            
            filename = os.path.basename(source_file)
            
            # Standard Heuristic
            hq = f"""
            LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
            MATCH (source:{source_label} {{ id: row['id'] }}) -- Simplified assumption
            MATCH (target:{rel.get('to_node_label')} {{ id: row['target_id'] }}) -- Simplified
            MERGE (source)-[r:{rel_type}]->(target)
            """
            # NOTE: Heuristic above is very generic and likely wrong for complex cases. 
            # Reusing original logic would be better but it was also generic.
            # Let's use the LLM to fix this usually!
            
            # Quick check for original heuristic logic re-implementation
            source_key = rel.get('from_node_column', 'id')
            target_key = rel.get('to_node_column', 'id')
            target_label = rel.get('to_node_label')
            
            hq = f"""
            LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
            MATCH (source:{source_label} {{ {source_key}: row['{source_key}'] }})
            MATCH (target:{target_label} {{ {target_key}: row['{target_key}'] }})
            MERGE (source)-[r:{rel_type}]->(target)
            """

            choice = input(f"{CYAN}Import Strategy? [H]euristic / [L]LM / [C]ompare: {RESET}").strip().upper()
            final_query = hq
            
            if choice == 'L' or choice == 'C':
                 lq = self._generate_llm_query(f"Import Relationship {rel_type} between {source_label} and {target_label}", rel)
                 if choice == 'L': final_query = lq
                 else:
                    print(f"\n{CYAN}--- Heuristic ---{RESET}\n{hq}")
                    print(f"\n{CYAN}--- LLM Generated ---{RESET}\n{lq}")
                    sel = input(f"\n{YELLOW}Select [H]euristic or [L]LM: {RESET}").strip().upper()
                    final_query = lq if sel == 'L' else hq
            
            self._execute_import(f"Rel {rel_type}", final_query)

    def _execute_import(self, label, query):
        result = graphdb.send_query(query)
        status = "ERROR" if isinstance(result, dict) and "error" in result else "SUCCESS"
        self.log_step(label, f"Query: {query}", status)

    def init_log(self):
        # Log init handled in __init__ now or via logging utils
        pass

    def build_graph(self):
        # self.init_log() # done via logging utils implicitly when writing
        print(f"\n{CYAN}--- 🏗️  Starting Graph Construction ---{RESET}")
        
        if not graphdb.connect():
            self.log_step("Connection", "Failed to connect to Neo4j", "ERROR")
            return False

        print(f"{YELLOW}🧨 Nuking Database (Clean Slate Policy)...{RESET}")
        graphdb.nuke_database()
        
        try:
            plan = self.load_construction_plan()
        except Exception as e:
            self.log_step("Load Plan", str(e), "ERROR")
            return False

        nodes = []
        rels = []
        if isinstance(plan, dict):
            if 'nodes' in plan and isinstance(plan['nodes'], list):
                 nodes = plan['nodes']
                 rels = plan['relationships']
            else:
                 for key, rule in plan.items():
                     if not isinstance(rule, dict): continue
                     ctype = rule.get('construction_type')
                     if ctype == 'node': nodes.append(rule)
                     elif ctype == 'relationship': rels.append(rule)
        
        self.create_constraints(nodes)
        self.import_nodes(nodes)
        self.import_relationships(nodes, rels)
        
        print(f"\n{GREEN}✅ Build Sequence Complete. Check {self.log_path}{RESET}")
        return True
