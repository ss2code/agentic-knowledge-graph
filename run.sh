#!/usr/bin/env bash

cd "$(dirname "$0")" || exit 1

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

MODE="${1:-interactive}"
shift 2>/dev/null

case "$MODE" in
  --web | web)
    echo "Starting Web UI..."
    streamlit run app.py "$@"
    ;;
  --cli | cli)
    echo "Starting CLI..."
    python3 orchestrator.py --cli "$@"
    ;;
  *)
    echo "Starting Interactive CLI..."
    python3 orchestrator.py "$@"
    ;;
esac
