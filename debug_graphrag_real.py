import asyncio
import os
import sys
import datetime
import traceback
import json
from services.graph_service import graphdb
from services.gemini_graphrag import GeminiLLM, GeminiEmbedder
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.components.pdf_loader import DataLoader
from neo4j_graphrag.experimental.components.types import PdfDocument, DocumentInfo

# Using same components as actual agent
from agents.kg_pipeline_agent import MarkdownDataLoader, RegexTextSplitter

# Configuration
LOG_FILE = "data/debug/graphrag_test.log"
TEST_FILE = "temp_debug.md"
MODEL_NAME = "gemini-3-pro-preview"

class DualLogger(object):
    """Writes to both stdout/stderr and a log file."""
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w") # Overwrite mode

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

async def run_test():
    # Setup Logging
    os.makedirs("data/debug", exist_ok=True)
    sys.stdout = DualLogger(LOG_FILE)
    sys.stderr = sys.stdout # Capture errors too
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"============================================================")
    print(f"🧪 GraphRAG Pipeline Debug Report")
    print(f"🕒 Timestamp: {timestamp}")
    print(f"============================================================\n")
    
    # 1. Configuration Check
    print(f"📋 TEST CONFIGURATION")
    print(f"   Model: {MODEL_NAME}")
    print(f"   DB Driver: {graphdb.uri}")
    
    # Connect DB
    if not graphdb.connect():
        print("❌ CRITICAL: Failed to connect to Neo4j")
        return

    # 2. Schema Setup
    schema = {
        "node_types": ["Person", "Organization"],
        "relationship_types": ["WORKS_FOR"]
    }
    print(f"   Schema: {json.dumps(schema, indent=4)}")

    # 3. Input Preparation
    input_text = "# Test Doc\n---\nElon Musk works for SpaceX."
    print(f"\n📄 INPUT TEXT")
    print(f"------------------------------------------------------------")
    print(input_text)
    print(f"------------------------------------------------------------")
    
    with open(TEST_FILE, "w") as f:
        f.write(input_text)

    # 4. Pipeline Initialization
    print(f"\n⚙️  INITIALIZING PIPELINE")
    llm = GeminiLLM(model_name=MODEL_NAME) 
    embedder = GeminiEmbedder()
    
    # Prompt similar to actual use
    prompt_template = """
    Extract entities: Person, Organization.
    Extract relationships: WORKS_FOR.
    Context:
    {text}
    
    Format: JSON with 'nodes' (id, label, properties) and 'relationships' (start_node_id, end_node_id, type, properties).
    IMPORTANT: Return ONLY valid JSON. Ensure 'properties' key exists. Use 'start_node_id' and 'end_node_id' for relationships.
    """
    
    pipeline = SimpleKGPipeline(
        llm=llm,
        driver=graphdb.driver,
        embedder=embedder,
        schema=schema,
        prompt_template=prompt_template,
        text_splitter=RegexTextSplitter("---"),
        pdf_loader=MarkdownDataLoader(),
        from_pdf=True
    )
    
    # 5. Execution
    try:
        print(f"\n🏃‍♂️ RUNNING PIPELINE (Async)...")
        print(f"(Standard Output from components will follow below)\n")
        
        result = await pipeline.run_async(file_path=TEST_FILE)
        
        print(f"\n✅ EXECUTION SUCCESS")
        print(f"============================================================")
        print(f"📊 RESULT SUMMARY")
        print(f"{json.dumps(result.result, indent=2)}")
        print(f"============================================================")
            
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
        print(f"\nEnd of Report.")

if __name__ == "__main__":
    asyncio.run(run_test())
