
import os
import shutil
import glob
import re
from datetime import datetime

def get_log_file_path(log_dir, module_name):
    """
    Returns a new timestamped log file path for a module.
    Also triggers rotation of *previous* logs for this specific module to backup.
    
    Format: debug_llm_<module_name>_<timestamp>.md
    """
    # 1. Rotate existing logs for this module BEFORE creating the new one
    rotate_module_specific_logs(log_dir, module_name)
    
    # 2. Generate new path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debug_llm_{module_name}_{timestamp}.md"
    return os.path.join(log_dir, filename)

def rotate_module_specific_logs(log_dir, module_name):
    """
    Moves ALL existing log files for a specific module to backup.
    Then enforces 'Keep One' policy in backup.
    """
    if not os.path.exists(log_dir):
        return

    backup_dir = os.path.join(log_dir, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Pattern to match: debug_llm_<module_name>_*.md OR debug_llm_<module_name>.md (legacy)
    # We use glob. But module_name might be a substring of another. 
    # So we construct specific patterns.
    
    # We look for files starting with the specific prefix
    prefix = f"debug_llm_{module_name}"
    
    for filename in os.listdir(log_dir):
        if not filename.endswith(".md"): continue
        
        # Check strict prefix match to differentiate e.g. "Agent" from "AgentHelper"
        if filename.startswith(prefix) and (len(filename) == len(prefix) + 3 or filename[len(prefix)] in ['_', '.']):
             # It matches. Move to backup.
             src = os.path.join(log_dir, filename)
             dst = os.path.join(backup_dir, filename)
             try:
                 shutil.move(src, dst)
             except Exception as e:
                 print(f"Failed to move {filename}: {e}")

    # Now Clean Backup (Keep Only Latest)
    ensure_single_backup_copy(backup_dir, module_name)

def ensure_single_backup_copy(backup_dir, module_name):
    """
    Scans backup_dir for files matching the module. 
    Keeps ONLY the one with the latest timestamp (lexicographically or mod time).
    Deletes others.
    """
    prefix = f"debug_llm_{module_name}"
    matching_files = []
    
    for filename in os.listdir(backup_dir):
        if filename.startswith(prefix) and filename.endswith(".md"):
             matching_files.append(filename)
    
    if len(matching_files) <= 1:
        return

    # Sort matching files. Assuming timestamp format YYYYMMDD_HHMMSS ensures string sort works for date.
    # Legacy files without timestamp will be 'smaller'/older usually if we just sort string, 
    # but strictly we should check creation time if needed. 
    # Given the new format uses YYYYMMDD, string sort is sufficient for new files.
    # We put them in ascending order. Last is newest.
    matching_files.sort()
    
    # Keep the last one (newest)
    to_delete = matching_files[:-1]
    
    for f in to_delete:
        try:
            os.remove(os.path.join(backup_dir, f))
            # print(f"Deleted old backup: {f}")
        except Exception as e:
            print(f"Failed to delete old backup {f}: {e}")

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
