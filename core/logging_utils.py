
import os
import shutil
import time
from datetime import datetime

def rotate_logs(log_dir):
    """
    Moves existing .md log files in log_dir to a 'backup' subdirectory with a timestamp suffix.
    Should be called once at startup.
    """
    if not os.path.exists(log_dir):
        return

    backup_dir = os.path.join(log_dir, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for filename in os.listdir(log_dir):
        if filename.endswith(".md") and filename.startswith("debug_llm_"):
            src = os.path.join(log_dir, filename)
            # e.g. debug_llm_IntentAgent.md -> debug_llm_IntentAgent_20231027_120000.md
            new_name = f"{os.path.splitext(filename)[0]}_{timestamp}.md"
            dst = os.path.join(backup_dir, new_name)
            try:
                shutil.move(src, dst)
                # print(f"Rotated {filename} to backup.")
            except Exception as e:
                print(f"Failed to rotate log {filename}: {e}")

def get_log_file_path(log_dir, module_name):
    """
    Returns the fixed log file path for a module.
    Format: debug_llm_<module_name>.md
    """
    filename = f"debug_llm_{module_name}.md"
    return os.path.join(log_dir, filename)

def log_llm_interaction(log_file_path, module_name, model_name, function_name, prompt, response, system_instruction=None):
    """
    Appends an LLM interaction to the specified log file in Markdown format.
    """
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # If file is empty, write header
    if not os.path.exists(log_file_path) or os.path.getsize(log_file_path) == 0:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"# LLM Debug Log: {module_name}\n\n")

    entry = f"""
## {timestamp} | Function: `{function_name}`

**Model**: `{model_name}`

### Prompt
```text
{prompt}
```
"""
    if system_instruction:
        entry += f"""
### System Instruction
```text
{system_instruction}
```
"""

    entry += f"""
### Response
```text
{response}
```

---
"""
    
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(entry)
        
    print(f"\033[96m[DEBUG] Log updated: {os.path.basename(log_file_path)} (Func: {function_name})\033[0m")
