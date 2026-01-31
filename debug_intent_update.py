from state_manager import StateManager
import time
import json
import os

print("--- Testing StateManager Intent Update ---")

# 1. Setup Data Dir
os.makedirs('data', exist_ok=True)
json_path = 'data/user_intent.json'

# 2. Write Initial State
initial_data = {"intent": "Old Intent", "primary_entities": ["OldEntity"]}
with open(json_path, 'w') as f:
    json.dump(initial_data, f)

sm = StateManager()
curr = sm.get_current_intent()
print(f"Current Intent (Step 1): {curr.get('intent')}")
assert curr.get('intent') == "Old Intent"

# 3. Simulate Agent updating file
print(">> Simulating Agent Update... (Writing New Intent)")
new_data = {"intent": "New Intent", "primary_entities": ["NewEntity"]}
with open(json_path, 'w') as f:
    json.dump(new_data, f)
    f.flush()
    os.fsync(f.fileno())

# 4. Check StateManager again (Same Instance)
curr_2 = sm.get_current_intent()
print(f"Current Intent (Step 2): {curr_2.get('intent')}")

if curr_2.get('intent') == "New Intent":
    print("✅ SUCCESS: StateManager sees the update.")
else:
    print("❌ FAILURE: StateManager sees stale data.")
