from services.graph_service import graphdb
import json

def debug_schema():
    print("Connecting...")
    if not graphdb.connect():
        print("Failed to connect.")
        return

    print("Fetching Schema Visualization (APOC)...")
    schema = graphdb.get_schema_visualization()
    
    print("\n--- RAW SCHEMA ---")
    print(json.dumps(schema, indent=2, default=str))
    
    # Also manual check of Ingredient properties
    print("\n--- INGREDIENT SAMPLE ---")
    data = graphdb.send_query("MATCH (i:Ingredient) RETURN keys(i) as props LIMIT 1")
    print(data)

if __name__ == "__main__":
    debug_schema()
