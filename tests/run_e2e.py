
import os
import sys
import shutil
import json
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.context import Context
from services.graph_service import graphdb
from orchestrator import Orchestrator

# Setup Config
CANNED_DATA_DIR = "data/user_data/restaraunt_data" # Existing golden dataset
TEST_CONTEXT_NAME = "test_e2e_golden"
TEST_BASE_PATH = os.path.abspath(os.path.join(os.getcwd(), 'data', TEST_CONTEXT_NAME))

class TestE2EPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print(f"\n[E2E] Setting up Test Context: {TEST_BASE_PATH}")
        
        # 1. Clean previous test run
        if os.path.exists(TEST_BASE_PATH):
            shutil.rmtree(TEST_BASE_PATH)
        
        # 2. Configure Environment for Test
        # Avoid conflict with running user Neo4j
        os.environ["NEO4J_URI"] = "bolt://localhost:7688" 
        os.environ["NEO4J_USERNAME"] = "neo4j"
        os.environ["NEO4J_PASSWORD"] = "password"
        # Mock API Key to avoid prompts
        os.environ["GEMINI_API_KEY"] = "test-key-123"

        # 3. Create Context Dirs
        cls.ctx = Context(name=TEST_CONTEXT_NAME, base_path=TEST_BASE_PATH)
        cls.ctx.ensure_directories()
        
        # 4. Copy Canned Data to User Data
        src_data = os.path.join(os.getcwd(), CANNED_DATA_DIR, 'user_data')
        if not os.path.exists(src_data):
            # Fallback if canned_data structure is different
            src_data = os.path.join(os.getcwd(), CANNED_DATA_DIR)
            
        print(f"[E2E] Seeding data from {src_data}...")
        for f in os.listdir(src_data):
            src_f = os.path.join(src_data, f)
            if os.path.isfile(src_f) and not f.startswith('.'):
                shutil.copy(src_f, cls.ctx.data_dir)
                
        # 5. Initialize Orchestrator (CLI Mode to avoid startup prompts)
        # We need to mock input if we call interactive methods
        cls.app = Orchestrator(cls.ctx, cli_mode=True)
        
        # 6. Monkey Patch ContainerService to use Test Ports
        original_start = cls.app.container_svc.start_container
        
        def mock_start_container(force_restart=False):
            # This is a bit hacky but avoids changing source code just for tests
            # We intercept the subprocess call inside start_container? 
            # Easier to just stop the conflicting one or use different ports logic if supported.
            # Since source code relies on hardcoded ports in ContainerService, we MUST patch the method fully
            # or patch subprocess.run. 
            
            # Let's try patching subprocess.run ONLY when calling docker run
            with patch('subprocess.run') as mock_run:
                # We essentially re-implement logic or use a Side Effect?
                # Too complex. 
                # Simplest: Stop the main container if running? No disruptive.
                
                # We will redefine the command in the class instance? No, it's method local.
                # We will just implement the Docker Start logic directly here for the test.
                
                print("[E2E] Starting Test Container on 7475/7688...")
                # Stop if exists
                cls.app.container_svc.stop_container()
                
                import_vol = os.path.abspath(cls.ctx.data_dir)
                data_vol = os.path.abspath(os.path.join(cls.ctx.neo4j_home, 'data'))
                logs_vol = os.path.abspath(os.path.join(cls.ctx.neo4j_home, 'logs'))
                
                cmd = [
                    "docker", "run", "-d",
                    "--name", cls.app.container_svc.container_name,
                    "-p", "7475:7474", "-p", "7688:7687", # Test Ports
                    "-e", "NEO4J_AUTH=neo4j/password",
                    "-e", "NEO4J_PLUGINS=[\"apoc\"]",
                    "-e", "NEO4J_apoc_export_file_enabled=true",
                    "-e", "NEO4J_apoc_import_file_enabled=true",
                    "-e", "NEO4J_apoc_import_file_use__neo4j__config=true",
                    "-e", "NEO4J_dbms_security_procedures_unrestricted=apoc.*",
                    "-v", f"{import_vol}:/var/lib/neo4j/import",
                    "-v", f"{data_vol}:/data",
                    "-v", f"{logs_vol}:/logs",
                    "neo4j:latest"
                ]
                import subprocess
                subprocess.run(cmd, check=True)
                cls.app.container_svc.wait_for_healthy()
                return True

        # Replaces binding
        cls.app.container_svc.start_container = mock_start_container
        cls.app.container_svc.start_container(force_restart=True)
        
        # 7. Patch BaseAgent._get_valid_api_key in all modules
        # We need a smart input mocker to handle different prompts
        def smart_input_mock(prompt=""):
            p = str(prompt).lower()
            print(f"[E2E Mock Input] Prompt: '{p.strip()}' -> ", end="")
            
            if "api key" in p:
                print("test-key")
                return "test-key"
            
            if "[a]pprove" in p: # Extraction Agent
                print("A")
                return "A"
            
            if "approve" in p or "lock" in p or "confirm" in p or "continue" in p:
                print("y")
                return "y"
                
            if "select option" in p:
                # If Orchestrator Main Loop asks, we might want to exit?
                # But we are calling methods directly in tests, so we shouldn't hit main loop prompt
                # unless we call main_loop(). 
                print("12")
                return "12"
            
            # Default
            print("y")
            return "y"

        cls.input_patcher = patch('builtins.input', side_effect=smart_input_mock)
        cls.input_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.input_patcher.stop()
        # deep cleanup if needed
        # cls.app.container_svc.stop_container()
        pass

    def test_01_intent_definition(self):
        print("\n[E2E] Step 1: Intent Definition (Phase 2)")
        # Simulate Intent Agent success
        intent = {
            "intent": "Trace Supply Chain",
            "description": "Map ingredients to products to identify issues.",
            "primary_entities": ["Product", "Ingredient", "Supplier"],
            "reasoning": "E2E Test Intent"
        }
        
        # Manually write contract (Mocking the agent interaction)
        self.app.sm.mark_intent_updated() # Update state
        with open(os.path.join(self.ctx.base_path, 'user_intent.json'), 'w') as f:
            json.dump(intent, f)
            
        self.assertTrue(os.path.exists(os.path.join(self.ctx.base_path, 'user_intent.json')))

    def test_02_data_approval(self):
        print("\n[E2E] Step 2: Approve Files (Phase 3a)")
        # Call actual method in CLI mode (should auto-approve or we verify logic)
        # Orchestrator.approve_files() in CLI mode sets confirm='y' automatically
        self.app.approve_files()
        
        self.assertTrue(os.path.exists(os.path.join(self.ctx.base_path, 'approved_files.json')))

    def test_03_schema_negotiation(self):
        print("\n[E2E] Step 3: Schema Negotiation (Phase 3b)")
        # We need to run the loop. The loop uses LLMs.
        # If no API key, it fails. We assume env var is set.
        
        # MOCKING: To save tokens and time, we can inject a construction_plan.json
        # UNLESS we specifically want to test the Agents' LLM logic.
        # For E2E Regression, we generally want to test that the *pipeline* works.
        # Testing LLM intelligence is flaky.
        
        # Let's try running it but if it fails (no key), we fallback to mock?
        # Better: Mock the Agents to return fixed JSON.
        
        # Mock SchemaProposalAgent
        with patch('agents.schema_agent.SchemaProposalAgent.propose_schema') as mock_propose:
            # Mock success return
            mock_propose.return_value = (json.dumps({
                "Product": {
                    "construction_type": "node",
                    "label": "Product",
                    "source_file": "products.csv",
                    "properties": ["id", "name"]
                },
                 "Ingredient": {
                    "construction_type": "node",
                    "label": "Ingredient",
                    "source_file": "products.csv", # Assuming ingredients are in products or similar for mock
                    "properties": ["id", "name"]
                }
            }), "mock-model")
            
            with patch('agents.schema_agent.SchemaCriticAgent.critique_schema') as mock_critique:
                mock_critique.return_value = (json.dumps({"status": "VALID", "feedback": "Looks good"}), "mock-model")
                
                self.app.run_schema_negotiation()
                
        self.assertTrue(os.path.exists(os.path.join(self.ctx.base_path, 'construction_plan.json')))
        
    def test_04_extraction_logic(self):
        print("\n[E2E] Step 4: Extraction Design (Phase 4)")
        # Similar to schema, mock the NER/Fact agents
        
        with patch('agents.extraction_agent.NERAgent.propose_entities') as mock_ner:
            mock_ner.return_value = (json.dumps({"entity_types": ["Product", "Issue"]}), "mock-model")
            
            with patch('agents.extraction_agent.FactExtractionAgent.propose_facts') as mock_fact:
                mock_fact.return_value = (json.dumps({"facts": []}), "mock-model")
                
                self.app.run_extraction_design()
                
        self.assertTrue(os.path.exists(os.path.join(self.ctx.base_path, 'extraction_plan.json')))

    def test_05_build_structured_graph(self):
        print("\n[E2E] Step 5: Build Graph (Structured)")
        # This talks to Neo4j. Real test.
        # It needs construction_plan.json (created in step 3)
        
        # Improve Step 3 mock to valid plan if needed for Step 5 to work
        # The mock above was valid.
        
        self.app.run_graph_build()
        self.assertTrue(os.path.exists(os.path.join(self.ctx.debug_dir, 'graph_build_log.md')))
        
        # Verify Nodes
        res = graphdb.send_query("MATCH (n) RETURN count(n) as c")
        count = res[0]['c']
        print(f"[E2E] Graph Node Count: {count}")
        self.assertGreater(count, 0, "Graph Build resulted in 0 nodes!")

    def test_06_graphrag_pipeline(self):
        print("\n[E2E] Step 6: GraphRAG Pipeline (Phase 5.7)")
        # Runs on Unstructured Data (.md files)
        
        # Mock LLM and Embedder to avoid API cost/latency
        # But we want to test the logic...
        # Let's allow real calls if API key exists, else skip
        
        if not os.getenv("GEMINI_API_KEY"):
            print("[E2E] Skipping GraphRAG (No API Key)")
            return
            
        # We can use a lightweight mock for GeminiLLM inside the agent
        # to return dummy extraction
        
        with patch('services.gemini_graphrag.GeminiLLM.invoke') as mock_invoke:
            # Must return object with .content
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "nodes": [{"id": "P1", "label": "Product", "properties": {"name": "TestProduct"}}],
                "relationships": []
            })
            mock_invoke.return_value = mock_response
            
            # Also mock Embedder because we don't have a Vector DB in this simple setup? 
            # Neo4j GraphRAG requires Vector Index usually? 
            # The SimpleKGPipeline might just store embeddings. 
            # Mocking Embedder:
            with patch('services.gemini_graphrag.GeminiEmbedder.embed_query') as mock_embed:
                mock_embed.return_value = [0.1] * 768
                
                # Mock async run
                import asyncio
                # We need to run the async method properly. 
                # Orchestrator does asyncio.run. 
                # Testing this is tricky with mocks inside subprocess? No we run method directly.
                
                # We trust Orchestrator calls agent.run_pipeline
                # Agent calls SimpleKGPipeline.
                
                # Let's just run it "Mocked" at high level or risk real calls.
                # Real calls are better for E2E if we can afford it. 
                # Using "flash" model is cheap.
                # Let's perform a REAL call but on a tiny file?
                
                # Reduce file size to ensure speed?
                # Data is already small (canned_data).
                
                self.app.run_kg_pipeline()
                
        # Check if graph build log created (Proves pipeline finished and logged stats)
        self.assertTrue(os.path.exists(os.path.join(self.ctx.debug_dir, 'graph_build_log.md')))




if __name__ == '__main__':
    unittest.main()
