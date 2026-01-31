import json
import os
import time
from services.graph_service import graphdb, CYAN, GREEN, YELLOW, RED, RESET
from agents.schema_agent import BaseAgent

class GraphBuilderAgent(BaseAgent):
    """
    Agent responsible for importing structured data (from CSV/JSON) into Neo4j
    based on the Construction Plan.
    """
    def __init__(self, api_key=None, verbose=True, context=None):
        """
        Initialize the Graph Builder.

        Args:
            api_key (str): (Not heavily used here as this agent mocks LLM calls typically).
            verbose (bool): Console verbosity.
            context (Context): The application context object.
        """
        super().__init__(api_key=api_key) 
        self.verbose = verbose
        self.context = context
        # Use context path if available, else legacy 'data'
        self.data_dir = context.data_dir if context else 'data'
        self.base_dir = context.base_path if context else 'data'
        
        self.log_path = os.path.join(self.base_dir, 'debug', 'graph_build_log.md')

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
        """
        Loads the approved Construction Plan (Schema).

        Returns:
            dict: The schema definition.
        """
        # Plan is typically in the base of the context/data dir
        path = os.path.join(self.base_dir, 'construction_plan.json')
        if not os.path.exists(path):
            # Fallback for now if not found in context root
            path = os.path.join('data', 'construction_plan.json')
            
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

    def import_nodes(self, nodes):
        self.log_step("Node Import", "Starting node batch import...")
        for node in nodes:
            label = node['label']
            source_file = node.get('source_file')
            if not source_file: continue
                
            unique_id = node.get('unique_column_name', node.get('unique_id', 'id'))
            props = node.get('properties', [])
            
            # Docker filepath: file:///filename (since we mount user_data to /import)
            # source_file usually is just the filename. Ensure we don't duplicate paths.
            filename = os.path.basename(source_file)
            
                
            # Check for generic "Split" rule (Simple Heuristic for now, or use LLM to generate query if we were fully dynamic)
            rule = node.get('transformation_rule', '')
            if "split" in rule.lower() and "ingredients" in rule.lower():
                # Special handling for splitting list columns into nodes
                source_col = "ingredients" # Inferred from rule or plan should have 'source_column'
                query = f"""
                LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
                UNWIND split(row['{source_col}'], ',') AS item
                WITH trim(item) as cleaned_item
                WHERE cleaned_item IS NOT NULL AND cleaned_item <> ''
                MERGE (n:{label} {{ {unique_id}: cleaned_item }})
                """
            elif source_file.endswith('.txt'):
                text_prop = next((p for p in props if 'text' in p or 'content' in p), 'text')
                query = f"""
                LOAD CSV FROM 'file:///{filename}' AS line
                WITH line, linenumber() AS ln
                WHERE line[0] IS NOT NULL
                MERGE (n:{label} {{ {unique_id}: toString(ln) }})
                SET n.{text_prop} = line[0]
                """
            else:
                query = f"""
                LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
                MERGE (n:{label} {{ {unique_id}: row['{unique_id}'] }})
                """
                set_parts = [f"n.{p} = row['{p}']" for p in props if p != unique_id]
                if set_parts: query += f"\nSET {', '.join(set_parts)}"
            
            result = graphdb.send_query(query)
            status = "ERROR" if isinstance(result, dict) and "error" in result else "SUCCESS"
            self.log_step(f"Import {label}", f"File: {filename}\nQuery: {query}", status)

    def import_relationships(self, nodes, relationships):
        self.log_step("Relationship Import", "Starting relationship import...")
        node_map = {n['label']: n for n in nodes}
        
        for rel in relationships:
            rel_type = rel.get('relationship_type', rel.get('type'))
            source_label = rel.get('from_node_label', rel.get('source_node'))
            target_label = rel.get('to_node_label', rel.get('target_node'))
            source_key = rel.get('from_node_column', 'id')
            target_key = rel.get('to_node_column', 'id')
            
            # Resolve source file
            source_file = rel.get('source_file')
            if not source_file:
                 source_node_def = node_map.get(source_label, {})
                 source_file = source_node_def.get('source_file')
            
            if not source_file: continue
            
            filename = os.path.basename(source_file)
            rule = rel.get('rule', 'Standard match')
            
            if "split" in rule.lower() and "ingredients" in rule.lower():
                 # Example special handling
                 delim_col = "ingredients"
                 query = f"""
                 LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
                 MATCH (source:{source_label} {{ {source_key}: row['{source_key}'] }})
                 UNWIND split(row['{delim_col}'], ',') AS item
                 WITH source, trim(item) AS cleaned_item
                 MERGE (target:{target_label} {{ {target_key}: cleaned_item }})
                 MERGE (source)-[r:{rel_type}]->(target)
                 """
                 self._execute_import(f"Rel Split {rel_type}", query)
            else:
                 # Standard
                 query = f"""
                 LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
                 MATCH (source:{source_label} {{ {source_key}: row['{source_key}'] }})
                 MATCH (target:{target_label} {{ {target_key}: row['{target_key}'] }})
                 MERGE (source)-[r:{rel_type}]->(target)
                 """
                 self._execute_import(f"Rel {rel_type}", query)

    def _execute_import(self, label, query):
        result = graphdb.send_query(query)
        status = "ERROR" if isinstance(result, dict) and "error" in result else "SUCCESS"
        self.log_step(f"Import {label}", f"Query: {query}", status)

    def init_log(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, 'w') as f:
            f.write(f"# Graph Build Log - {time.strftime('%Y-%m-%d')}\n")

    def build_graph(self):
        self.init_log()
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

        # Parse Plan (Support dict style)
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
