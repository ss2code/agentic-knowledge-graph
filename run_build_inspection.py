from agents.graph_builder import GraphBuilderAgent
import os

from services.graph_service import graphdb

# Ensure we are in the right dir for relative paths (simulating orchestrator)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("--- Triggering Graph Build & Inspection ---")
print("🧨 Nuking Database...")
graphdb.nuke_database()

builder = GraphBuilderAgent()
success = builder.build_graph()

if success:
    print("Graph Build & Inspection COMPLETED.")
else:
    print("Graph Build FAILED.")
