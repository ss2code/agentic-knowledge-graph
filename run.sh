#!/usr/bin/env bash
# run.sh — prj_agentBased_KG dispatcher
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "$(cd "$ROOT_DIR/.." && pwd)/scripts/regression_helpers.sh"

VENV="$ROOT_DIR/.venv"
PY="$VENV/bin/python"
LAUNCH_PORT="${STREAMLIT_PORT:-8501}"
REGRESSION_PORT="${REGRESSION_PORT:-8512}"

usage() {
  cat <<'EOF'
prj_agentBased_KG — Knowledge Graph orchestrator (Streamlit + Neo4j)

Usage:
  ./run.sh                      Interactive CLI (alias for --interactive)
  ./run.sh --ui                 Streamlit UI on http://127.0.0.1:8501
  ./run.sh --cli [args...]      Orchestrator CLI mode
  ./run.sh --interactive        Interactive orchestrator (default)
  ./run.sh --regression         Headless UI + Playwright smoke (no Neo4j needed)
  ./run.sh --help               This help

Notes:
  Full functionality needs a running Neo4j instance — set NEO4J_URI / NEO4J_USERNAME
  / NEO4J_PASSWORD and PROJECT_ANTHROPIC_API_KEY in your env. Regression only
  checks the UI shell renders.

Entrypoints:  app.py (UI)  orchestrator.py (CLI)
EOF
}

ensure_venv() {
  if [[ ! -x "$PY" ]]; then
    echo "[run] creating .venv with uv..."
    uv venv "$VENV"
    uv pip install --python "$PY" -r requirements.txt
  fi
}

ensure_playwright() {
  if ! "$PY" -c "import playwright" 2>/dev/null; then
    echo "[run] installing playwright..."
    uv pip install --python "$PY" playwright
    "$PY" -m playwright install chromium
  fi
}

cmd_ui() {
  ensure_venv
  source "$VENV/bin/activate"
  exec streamlit run app.py --server.port "$LAUNCH_PORT" "$@"
}

cmd_cli() {
  ensure_venv
  exec "$PY" orchestrator.py --cli "$@"
}

cmd_interactive() {
  ensure_venv
  exec "$PY" orchestrator.py "$@"
}

_REGRESSION_PID=""
_cleanup_regression() { kill_tree "${_REGRESSION_PID:-}"; }

cmd_regression() {
  local start=$(date +%s)
  ensure_venv
  ensure_playwright

  local url="http://127.0.0.1:${REGRESSION_PORT}"
  trap _cleanup_regression EXIT INT TERM

  echo "[regression] booting Streamlit headless on $url ..."
  export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
  "$VENV/bin/streamlit" run app.py \
      --server.port "$REGRESSION_PORT" \
      --server.headless true \
      --server.fileWatcherType none \
      --browser.gatherUsageStats false \
      > .regression-streamlit.log 2>&1 &
  _REGRESSION_PID=$!

  if ! wait_for_url "${url}/_stcore/health" 45; then
    write_regression_report "FAIL" "streamlit failed to start within 45s" $(( $(date +%s) - start ))
    return 1
  fi

  "$PY" "$ROOT_DIR/../scripts/streamlit_regression.py" \
      --url "$url" \
      --title-contains "KG Orchestrator" \
      --selector '[data-testid="stSidebar"] h1' \
      --selector 'h1, h2' \
      --screenshot "$ROOT_DIR/.regression-screenshot.png"
  local rc=$?
  local dur=$(( $(date +%s) - start ))

  if [[ $rc -eq 0 ]]; then
    write_regression_report "PASS" "UI shell loaded — full flow needs live Neo4j" "$dur"
  elif [[ $rc -eq 2 ]]; then
    write_regression_report "SKIP" "playwright unavailable" "$dur"
    return 0
  else
    write_regression_report "FAIL" "see .regression-streamlit.log" "$dur"
  fi
  return $rc
}

case "${1:---interactive}" in
  --ui|ui) shift; cmd_ui "$@" ;;
  --cli|cli) shift; cmd_cli "$@" ;;
  --interactive|interactive|"") shift 2>/dev/null || true; cmd_interactive "$@" ;;
  --regression|regression) cmd_regression ;;
  --help|-h|help) usage ;;
  *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
esac
