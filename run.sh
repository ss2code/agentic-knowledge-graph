#!/usr/bin/env bash

# Navigate to the directory containing this script
cd "$(dirname "$0")" || exit 1

# Activate the virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Warning: .venv/bin/activate not found. Running with system Python."
fi

# Run the orchestrator, passing any arguments provided to the script
echo "Starting Agentic Knowledge Graph Orchestrator..."
python3 orchestrator.py "$@"
