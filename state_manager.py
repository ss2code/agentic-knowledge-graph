import json
import os
import datetime

STATE_FILE = 'data/system_state.json'
INTENT_FILE = 'data/user_intent.json'

class StateManager:
    def __init__(self, base_path='data'):
        self.base_path = base_path
        self.state_file = os.path.join(base_path, 'system_state.json')
        self.intent_file = os.path.join(base_path, 'user_intent.json')
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        
        # Default State
        return {
            "intent_defined": False,
            "files_approved": False,
            "schema_status": "PENDING", # PENDING, VALID, STALE
            "graph_status": "PENDING",   # PENDING, BUILT, STALE
            "last_updated": str(datetime.datetime.now())
        }

    def save_state(self):
        self.state["last_updated"] = str(datetime.datetime.now())
        os.makedirs(self.base_path, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def mark_intent_updated(self):
        """Called when IntentAgent saves a new intent."""
        self.state["intent_defined"] = True
        self.state["schema_status"] = "STALE" # Invalidate downstream
        self.state["graph_status"] = "STALE"
        self.save_state()

    def mark_files_approved(self):
        self.state["files_approved"] = True
        self.state["schema_status"] = "STALE"
        self.state["graph_status"] = "STALE"
        self.save_state()

    def mark_schema_valid(self):
        self.state["schema_status"] = "VALID"
        self.state["graph_status"] = "STALE"
        self.save_state()

    def mark_graph_built(self):
        self.state["graph_status"] = "BUILT"
        self.save_state()

    def mark_extraction_designed(self):
        """Called when Extraction Schema is generated."""
        self.state["extraction_designed"] = True
        self.save_state()

    def mark_graphrag_complete(self):
        """Called when GraphRAG pipeline finishes."""
        self.state["graphrag_status"] = "COMPLETE"
        self.save_state()

    def get_current_intent(self):
        if os.path.exists(self.intent_file):
            try:
                with open(self.intent_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading intent file: {e}")
                return None
        return None

    def get_current_schema(self):
        schema_path = os.path.join(self.base_path, 'construction_plan.json')
        if os.path.exists(schema_path):
            try:
                with open(schema_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading schema file: {e}")
                return None
        return None

if __name__ == "__main__":
    # Test
    sm = StateManager()
    print("Current State:", sm.state)
    sm.mark_intent_updated()
    print("Updated State:", sm.state)
