import os
import shutil
import sys

def setup_test_data():
    source_dir = os.path.abspath("data/user_data")
    target_dir = os.path.abspath("tests/canned_data/user_data")
    
    print(f"Setting up test data...")
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    
    if os.path.exists(target_dir):
        print("Cleaning previous test data...")
        shutil.rmtree(target_dir)
        
    try:
        shutil.copytree(source_dir, target_dir)
        print("✅ Test data ready in tests/canned_data")
        
        # Also copy config/schema if present to replicate state
        # (Optional based on requirements, but good for canned)
        
    except Exception as e:
        print(f"❌ Failed to copy data: {e}")

if __name__ == "__main__":
    setup_test_data()
