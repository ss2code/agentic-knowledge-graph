# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Interactive UI (recommended for development)
python3 orchestrator.py

# Web UI (Streamlit)
./run.sh web

# CLI build for a specific context
python3 orchestrator.py --context data/my_project --cli --action build

# Run unit tests (Neo4j must NOT be running on default ports)
pytest

# Run integration tests (requires PROJECT_ANTHROPIC_API_KEY)
pytest tests/test_anthropic_integration.py -v

# Run a single test file
pytest tests/test_key_logic.py -v

# Full end-to-end integration test (uses Neo4j on port 7688)
python3 tests/run_e2e.py

# Configure pre-push hook (run once per clone)
git config core.hooksPath .githooks

# Force-replace Neo4j container (destructive - breaks context volumes)
./update_neo4j.sh
```

**Environment variables required:**
- `PROJECT_ANTHROPIC_API_KEY` — used by all LLM agents; agents run in simulation mode (return empty JSON stubs) if missing
- `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` — default to `bolt://localhost:7687` / `neo4j` / `password`

## Architecture

### Pipeline Stages (in order)

1. **Intent** (`agents/intent_agent.py`) — Interactive interview; saves `user_intent.json`
2. **File Approval** (`orchestrator.py:approve_files`) — Scans `<context>/user_data/`; saves `approved_files.json`
3. **Schema Negotiation** (`agents/schema_agent.py:SchemaRefinementLoop`) — LLM iterates on graph schema; saves `construction_plan.json`
4. **Extraction Design** (`agents/extraction_agent.py:ExtractionSchemaLoop`) — NER + fact extraction planning; saves `extraction_plan.json`
5. **Graph Build** (`agents/graph_builder.py:GraphBuilderAgent`) — Reads structured files + `construction_plan.json`; writes to Neo4j

`KgPipelineAgent` (`agents/kg_pipeline_agent.py`) is an optional alternative for unstructured text files using the `neo4j_graphrag` library's `SimpleKGPipeline`.

### Key Classes

- **`Context`** (`core/context.py`) — Dataclass holding all paths for a project run. Properties: `.data_dir` (inputs), `.debug_dir` (LLM logs), `.neo4j_home` (Docker volume), `.output_dir`, `.config_dir`. Created via `Context.from_path(path)`.
- **`Orchestrator`** (`orchestrator.py`) — Central controller. Owns `StateManager` and `ContainerService`; dispatches to agents. Auto-starts Neo4j on init.
- **`StateManager`** (`state_manager.py`) — Reads/writes `system_state.json`. Invalidates downstream stages when upstream changes (e.g., editing intent marks schema STALE).
- **`BaseAgent`** (`agents/schema_agent.py`) — Parent for all LLM-backed agents. Wraps `AnthropicProvider`; handles retry with exponential backoff on `RateLimitError`. Runs in simulation mode (returns empty JSON) when `PROJECT_ANTHROPIC_API_KEY` is not set.
- **`AnthropicProvider`** (`services/llm_provider.py`) — Provider abstraction. `BaseLLMProvider` ABC + `AnthropicProvider` implementation. Models: `claude-sonnet-4-6` (default), `claude-haiku-4-5-20251001`.
- **`AnthropicLLM` / `SentenceTransformerEmbedder`** (`services/anthropic_graphrag.py`) — Adapters implementing `neo4j_graphrag`'s `LLMInterface` / `Embedder` for use in `SimpleKGPipeline`.
- **`ContainerService`** (`services/container_service.py`) — Wraps Docker CLI to start/stop per-context Neo4j containers named `neo4j-<context.name>`.
- **`GraphService`** (`services/graph_service.py`) — Singleton `graphdb` instance. Wraps Neo4j Bolt driver; used by all agents for Cypher queries.

### Context Isolation

Each project gets its own directory tree. Multiple contexts can coexist with separate Docker containers and Neo4j volumes:
```
<context>/
  user_data/          ← input files (CSV, MD, TXT)
  construction_plan.json
  extraction_plan.json
  approved_files.json
  user_intent.json
  system_state.json
  neo4j_home/         ← Docker volume mount
  debug/              ← per-agent timestamped LLM logs (debug_llm_<Agent>_<ts>.md)
  output/             ← GraphML dumps, schema visualizations
```

### Debug Logging

`core/logging_utils.py` manages per-agent log files. On each agent init, existing logs for that module are rotated to `debug/backup/` (keeping only the latest backup). Logs record full prompt + response for every LLM call.

## Key Conventions

- **Neo4j Management**: Always let `ContainerService` control Docker. Volumes map to `<context>/neo4j_home/`. Do not manually start Neo4j on port 7687 when running tests.
- **`construction_plan.json`**: The central artifact linking schema design to graph construction. Format is a dict keyed by rule ID with `construction_type: node|relationship` entries.
- **Testing**: Unit tests in `tests/` use `unittest.mock` and do not require Neo4j. The E2E test (`tests/run_e2e.py`) uses port 7688 to avoid collision with a running instance.
- **Sample runs**: `data/sample_runs/restaraunt_data/` contains preserved debug logs and schema artifacts for reference.

## Code Style

- **Commits**: Use Conventional Commits — `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:` prefixes.
- **Formatting/linting**: Run `ruff check .` and `ruff format .` before committing (install with `pip install ruff` if needed). No config file yet; defaults are fine.
- **Streamlit widgets**: Always add an explicit `key=` parameter — never rely on position-based auto-keys.
<!-- pwiki:claude-rules:start -->
## pwiki

This repo uses pwiki in an offline-first way.
- Durable content lives in `pwiki/`
- `pwiki cleanup offline-preserve` removes pwiki-managed overlays and keeps markdown content
- If graph is enabled, Claude may read `pwiki/.graph/STRUCTURE_REPORT.md` before targeted source reads
<!-- pwiki:claude-rules:end -->
