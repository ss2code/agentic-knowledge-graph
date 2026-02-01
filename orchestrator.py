import sys
import os
import json
import argparse
import time
import warnings
# Suppress Pydantic V1 warnings from Neo4j/LangChain libraries
try:
    warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
    warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality isn't compatible.*")
except:
    pass

from core.context import Context
from services.container_service import ContainerService
from state_manager import StateManager
from agents.schema_agent import SchemaRefinementLoop
from agents.extraction_agent import ExtractionSchemaLoop
from agents.graph_builder import GraphBuilderAgent
from agents.kg_pipeline_agent import KgPipelineAgent
from agents.visualizer_agent import VisualizerAgent
from services.graph_service import graphdb

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

class Orchestrator:
    def __init__(self, context: Context, cli_mode=False):
        self.context = context
        self.cli_mode = cli_mode
        self.sm = StateManager() 
        self.container_svc = ContainerService(context)
        self.api_key = self._setup_api_key()
        
        self.context.ensure_directories()
        
        # Rotate logs on startup
        from core.logging_utils import rotate_logs
        if os.path.exists(self.context.debug_dir):
            rotate_logs(self.context.debug_dir)
        
        if not self.container_svc.is_running():
            print(f"{YELLOW}Neo4j is not running for this context. Starting...{RESET}")
            self.container_svc.start_container()

    def _setup_api_key(self):
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            if self.cli_mode:
                 print(f"{YELLOW}⚠️ GEMINI_API_KEY not found.{RESET}")
                 return None
                 
            print(f"{YELLOW}⚠️ GEMINI_API_KEY not found in environment.{RESET}")
            try:
                key = input(f"{CYAN}Enter Gemini API Key (visible): {RESET}").strip()
            except:
                key = ""
        
        if key:
            os.environ["GEMINI_API_KEY"] = key
            return key
        else:
            print(f"{RED}No key provided. Agents will run in SIMULATION MODE where possible.{RESET}")
            return None

    def clear_screen(self):
        if not self.cli_mode:
            os.system('cls' if os.name == 'nt' else 'clear')

    def print_status(self):
        s = self.sm.state
        print(f"\n{CYAN}--- 🏗️  Agentic KG Orchestrator ---{RESET}")
        print(f"Context: {GREEN}{self.context.name}{RESET} ({self.context.base_path})")
        
        intent_exists = os.path.exists(os.path.join(self.context.base_path, 'user_intent.json'))
        intent_icon = "✅" if intent_exists else "❌"
        print(f"Intent Definition:   {intent_icon}  {'Defined' if intent_exists else 'Not Defined'}")
        
        approved_exists = os.path.exists(os.path.join(self.context.base_path, 'approved_files.json'))
        files_icon = "✅" if approved_exists else "❌"
        print(f"Data Ingestion:      {files_icon}  {'Approved' if approved_exists else 'Not Approved'}")

        plan_exists = os.path.exists(os.path.join(self.context.base_path, 'construction_plan.json'))
        schema_status = "VALID" if plan_exists else "PENDING"
        schema_color = GREEN if schema_status == "VALID" else RED
        print(f"Schema Design:       {schema_color}{schema_status}{RESET}")
        
        ext_path = os.path.join(self.context.base_path, "extraction_plan.json")
        ext_status = "DONE" if os.path.exists(ext_path) else "PENDING"
        ext_color = GREEN if ext_status == "DONE" else RED
        print(f"Extraction Logic:    {ext_color}{ext_status}{RESET}")

        graph_log = os.path.join(self.context.base_path, 'debug', 'graph_build_log.md')
        graph_status = "BUILT" if os.path.exists(graph_log) else "PENDING"
        graph_color = GREEN if graph_status == "BUILT" else RED
        print(f"Graph Construction:  {graph_color}{graph_status}{RESET}")
        
        print("-----------------------------------")

    def approve_files(self):
        print(f"\n{YELLOW}>> Scanning {self.context.data_dir}...{RESET}")
        
        files = [f for f in os.listdir(self.context.data_dir) if not f.startswith('.')]
        if not files:
            print(f"{RED}No files found in {self.context.data_dir}.{RESET}")
            return

        print(f"{CYAN}Found the following files:{RESET}")
        for f in files:
            print(f" - {f}")
        
        if self.cli_mode:
            confirm = 'y'
        else:
            confirm = input(f"\n{GREEN}Approve these files for Graph Construction? (y/n): {RESET}").strip().lower()
            
        if confirm == 'y':
            approved_data = {"files": [os.path.join(self.context.data_dir, f) for f in files]}
            save_path = os.path.join(self.context.base_path, 'approved_files.json')
            with open(save_path, 'w') as f:
                json.dump(approved_data, f, indent=2)
            self.sm.mark_files_approved()
            print(f"{GREEN}✅ Files approved and locked.{RESET}")
        else:
            print(f"{YELLOW}Approval cancelled.{RESET}")
        
        if not self.cli_mode:
            input(f"\n{CYAN}Press [Enter] to return...{RESET}")

    def run_intent_agent(self):
        print(f"\n{YELLOW}>> Launching IntentAgent...{RESET}")
        try:
             import subprocess
             # Pass --data_dir arg
             subprocess.run([sys.executable, "agents/intent_agent.py", "--data_dir", self.context.base_path], check=True)
             
             if os.path.exists(os.path.join(self.context.base_path, 'user_intent.json')):
                 self.sm.mark_intent_updated()
        except subprocess.CalledProcessError:
             print(f"{RED}Agent crashed.{RESET}")
        except KeyboardInterrupt:
             print(f"\n{YELLOW}Cancelled.{RESET}")

    def run_schema_negotiation(self):
        if not os.path.exists(os.path.join(self.context.base_path, 'user_intent.json')):
             print(f"{RED}Prerequisites not met. Define Intent first.{RESET}")
             return
        if not os.path.exists(os.path.join(self.context.base_path, 'approved_files.json')):
             print(f"{RED}Prerequisites not met. Approve Files first.{RESET}")
             return
        
        try:
            loop = SchemaRefinementLoop(api_key=self.api_key, data_dir=self.context.base_path)
            success = loop.run()
            if success:
                self.sm.mark_schema_valid()
        except KeyboardInterrupt:
             print(f"\n{YELLOW}Negotiation cancelled.{RESET}")
        except Exception as e:
            print(f"{RED}Crash: {e}{RESET}")
            
        if not self.cli_mode:
            input(f"\n{CYAN}Press [Enter] to return...{RESET}")

    def run_extraction_design(self):
        plan_path = os.path.join(self.context.base_path, 'construction_plan.json')
        if not os.path.exists(plan_path):
             print(f"{RED}Prerequisites not met. Complete Phase 3b (Schema Negotiation) first.{RESET}")
             return

        try:
            loop = ExtractionSchemaLoop(api_key=self.api_key, data_dir=self.context.base_path)
            loop.run()
            self.sm.mark_extraction_designed()
        except Exception as e:
            print(f"{RED}Crash: {e}{RESET}")
        
        if not self.cli_mode:
            input(f"\n{CYAN}Press [Enter] to return...{RESET}")

    def run_graph_build(self):
        plan_path = os.path.join(self.context.base_path, 'construction_plan.json')
        if not os.path.exists(plan_path) and not self.cli_mode:
             print(f"{RED}Prerequisites not met. Schema must be VALID.{RESET}")
             return

        try:
            print(f"{YELLOW}⚠️  WARNING: This will NUKE the existing Neo4j database.{RESET}")
            # Inject Context into Builder
            builder = GraphBuilderAgent(api_key=self.api_key, context=self.context)
            success = builder.build_graph()
            
            if success:
                self.sm.mark_graph_built()
        except Exception as e:
            print(f"{RED}Crash: {e}{RESET}")
        
        if not self.cli_mode:
            input(f"\n{CYAN}Press [Enter] to return...{RESET}")

    def run_kg_pipeline(self):
        print(f"\n{CYAN}--- 🚀 Unstructured Data Pipeline (GraphRAG) ---{RESET}")
        
        files = [f for f in os.listdir(self.context.data_dir) if f.endswith('.md') or f.endswith('.txt')]
        
        if not files:
            print(f"{RED}No .md or .txt files found in {self.context.data_dir}.{RESET}")
            return
            
        print(f"Found {len(files)} files: {files}")
        if not self.cli_mode:
            confirm = input(f"{CYAN}Run Pipeline and Entity Resolution? (y/n): {RESET}")
            if confirm.lower() != 'y': return
        
        try:
             # Pass base_path because user_data is implicit in the logic
             agent = KgPipelineAgent(api_key=self.api_key, data_dir=self.context.base_path)
             import asyncio
             asyncio.run(agent.run_pipeline(files))
             
             agent.resolve_entities()
             self.sm.mark_graphrag_complete()
             print(f"\n{GREEN}Pipeline Complete!{RESET}")
        except Exception as e:
             print(f"{RED}Pipeline Error: {e}{RESET}")
        
        if not self.cli_mode:
             input("Press [Enter]...")

    def run_visualization(self):
        try:
             viz = VisualizerAgent(context=self.context)
             viz.run()
        except Exception as e:
             print(f"{RED}Visualization Error: {e}{RESET}")
             
        if not self.cli_mode:
            input(f"\n{CYAN}Press [Enter] to return...{RESET}")
            
    def run_export(self):
        filename = f"{self.context.name}_dump.graphml"
        print(f"{YELLOW}Exporting to {filename}...{RESET}")
        if graphdb.export_graph(filename):
             src = os.path.join(self.context.data_dir, filename)
             dst = os.path.join(self.context.output_dir, filename)
             if os.path.exists(src):
                 os.replace(src, dst)
                 print(f"{GREEN}Dump saved to: {dst}{RESET}")
             else:
                 print(f"{RED}Could not find exported file at {src}{RESET}")
        
        if not self.cli_mode:
             input("Press [Enter]...")

    def run_inspect_graph(self):
        print(f"\n{CYAN}--- 🔍 Inspecting Graph Stats ---{RESET}")
        if not self.container_svc.is_running():
             print(f"{RED}DB not running.{RESET}")
             return

        # 1. Total Counts
        q = "MATCH (n) RETURN count(n) as c"
        res = graphdb.send_query(q)
        total = res[0]['c'] if res else 0
        print(f"Total Nodes: {total}")
        
        # 2. Counts by Label
        q2 = "MATCH (n) RETURN labels(n)[0] as label, count(n) as c ORDER BY c DESC"
        res2 = graphdb.send_query(q2)
        if res2:
            print("\nNodes by Label:")
            for r in res2:
                print(f"  - {r['label']}: {r['c']}")
                
        # 3. Recent Nodes
        print("\nLatest 5 extracted entities:")
        q3 = "MATCH (n:`__Entity__`) RETURN n ORDER BY elementId(n) DESC LIMIT 5"
        res3 = graphdb.send_query(q3)
        if res3:
            for r in res3:
                 node = r['n']
                 props = json.dumps(dict(node), default=str)
                 print(f"  - {props}")
        else:
             print("  (No entities found)")

        if not self.cli_mode:
            input(f"\n{CYAN}Press [Enter] to return...{RESET}")

    def run_load_and_visualize(self):
        print(f"\n{CYAN}--- 📂 Load & Visualize ---{RESET}")
        
        # Check output dir for graphml files
        dump_files = [f for f in os.listdir(self.context.output_dir) if f.endswith('.graphml')]
        
        if not dump_files:
             print(f"{RED}No .graphml files found in {self.context.output_dir}{RESET}")
             return

        print(f"Available Dumps:")
        for i, f in enumerate(dump_files):
            print(f" {i+1}. {f}")
            
        choice = input(f"\n{CYAN}Select Dump to Load [1-{len(dump_files)}]: {RESET}").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(dump_files):
                filename = dump_files[idx]
                
                # Copy from output to data_dir (which is mapped to /import)
                src = os.path.join(self.context.output_dir, filename)
                dst = os.path.join(self.context.data_dir, filename)
                
                import shutil
                shutil.copy2(src, dst)
                
                print(f"{YELLOW}Loading {filename}...{RESET}")
                # Nuke first?
                confirm = input(f"{RED}This will DELETE current DB. Continue? (y/n): {RESET}")
                if confirm.lower() == 'y':
                     graphdb.nuke_database()
                     if graphdb.import_graph(filename):
                         print(f"{GREEN}Load Complete.{RESET}")
                         self.run_visualization()
                     else:
                         print(f"{RED}Load Failed.{RESET}")
            else:
                print(f"{RED}Invalid Selection.{RESET}")
        except ValueError:
             print(f"{RED}Invalid Input.{RESET}")
             
        if not self.cli_mode:
            input(f"\n{CYAN}Press [Enter] to return...{RESET}")

    def run_cleanup_context(self):
        print(f"\n{RED}🧨 CLEANUP: This will DELETE all generated data for context '{self.context.name}'!{RESET}")
        print(f"Targets: {self.context.neo4j_home}, {self.context.output_dir}, {self.context.config_dir}")
        print("User Data will NOT be touched.")
        
        confirm = input(f"Type '{self.context.name}' to confirm: ")
        if confirm == self.context.name:
             import shutil
             try:
                 print("Stopping Container...")
                 self.container_svc.stop_container()
                 
                 print("Removing Directories...")
                 if os.path.exists(self.context.neo4j_home): shutil.rmtree(self.context.neo4j_home)
                 if os.path.exists(self.context.output_dir): shutil.rmtree(self.context.output_dir)
                 
                 # Also remove plans from base_path? 
                 reset_plans = input("Reset Plans (intent, construction, extraction)? (y/n): ").lower() == 'y'
                 if reset_plans:
                     for f in ['user_intent.json', 'construction_plan.json', 'extraction_plan.json', 'approved_files.json']:
                         p = os.path.join(self.context.base_path, f)
                         if os.path.exists(p): os.remove(p)
                 
                 # Reset state
                 self.sm = StateManager()
                 print(f"{GREEN}Cleanup Complete. Please restart orchestrator or select Build.{RESET}")
             except Exception as e:
                 print(f"{RED}Error during cleanup: {e}{RESET}")
        else:
             print("cancelled.")
             
        if not self.cli_mode:
            input(f"\n{CYAN}Press [Enter] to return...{RESET}")

    def run_text_to_cypher(self):
        from agents.text_to_cypher_agent import TextToCypherAgent
        
        print(f"\n{YELLOW}>> Launching Text-to-Cypher Agent...{RESET}")
        agent = TextToCypherAgent(api_key=self.api_key, debug_dir=self.context.debug_dir)
        agent.run_interactive_loop()

    def main_loop(self):
        while True:
            self.clear_screen()
            self.print_status()
            
            print("1. Define Intent (Intent Definition)")
            print("2. Review Contract (View Intent)") 
            print("3. Approve Files (Data Ingestion)")
            print("4. Negotiate Schema (Schema Design)")
            print("5. Design Extraction Logic (Extraction Logic)")
            print("6. Build/Refresh Graph (Structured Data)")
            print("7. Run Knowledge Discovery (GraphRAG/Unstructured)")
            print("8. Inspect Graph Stats (Visualization)")
            print("9. Load Dump & Visualize")
            print("10. Export Data Dump") 
            print("11. Clean Up Context (Reset)")
            print("12. Text-to-Cypher Interface")
            print("13. Exit")
            
            choice = input(f"\n{CYAN}Select Option [1-13]: {RESET}").strip()
            
            if choice == '1':
                self.run_intent_agent()
            elif choice == '2':
                 path = os.path.join(self.context.base_path, 'user_intent.json')
                 if os.path.exists(path):
                     with open(path) as f:
                         print(json.load(f))
                     input("Press [Enter]...")
            elif choice == '3':
                self.approve_files()
            elif choice == '4':
                self.run_schema_negotiation()
            elif choice == '5':
                 self.run_extraction_design()
            elif choice == '6':
                 self.run_graph_build()
            elif choice == '7':
                 self.run_kg_pipeline()
            elif choice == '8':
                 self.run_inspect_graph()
            elif choice == '9':
                 self.run_load_and_visualize()
            elif choice == '10':
                 self.run_export()
            elif choice == '11':
                 self.run_cleanup_context()
            elif choice == '12':
                 self.run_text_to_cypher()
            elif choice == '13':
                 print(f"\n{GREEN}Goodbye!{RESET}")
                 sys.exit(0)
            else:
                 print(f"{YELLOW}Feature not fully context-aware or implemented.{RESET}")
                 input("Press [Enter]...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic KG Orchestrator")
    parser.add_argument("--context", type=str, default="data", help="Path to context directory (default: ./data)")
    parser.add_argument("--reset-db", action="store_true", help="Force restart of Neo4j container")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (non-interactive)")
    parser.add_argument("--action", type=str, help="Action to run in CLI mode (build, visualize, export)")
    
    args = parser.parse_args()
    
    ctx = Context.from_path(args.context)
    app = Orchestrator(ctx, cli_mode=args.cli)
    
    if args.reset_db:
        app.container_svc.start_container(force_restart=True)
        
    if args.cli:
        if args.action == "build":
            app.run_graph_build()
        elif args.action == "visualize":
            app.run_visualization()
        elif args.action == "export":
            app.run_export()
        else:
            print(f"{RED}Unknown or missing action for CLI mode.{RESET}")
    else:
        app.main_loop()
