from agents.text_to_cypher_agent import TextToCypherAgent
import os

def test_init():
    print("Testing TextToCypherAgent Initialization...")
    try:
        # Mock API Key
        agent = TextToCypherAgent(api_key="dummy_key")
        print("✅ Initialization Successful.")
        
        # Check if log file created/handled
        if os.path.exists(agent.debug_log_path):
             print(f"✅ Log file initialized at {agent.debug_log_path}")
             
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        exit(1)

if __name__ == "__main__":
    test_init()
