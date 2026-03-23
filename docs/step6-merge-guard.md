# Step 6 (GraphRAG) — Merge Guard

> **Purpose:** This document exists to prevent regressions in Step 6 when merging other branches into main. It lists the exact invariants that must hold, the files involved, and how to verify after a merge.
>
> If you are an AI agent working on a branch that will merge into main: read this carefully. These constraints are non-negotiable. Violating any of them silently breaks the GraphRAG pipeline.

---

## Files You Must Not Break

These files are the critical path for Step 6. If your branch modifies any of them, verify every invariant below.

| File | Role | Danger level |
|------|------|-------------|
| `services/anthropic_graphrag.py` | LLM + embedder adapters for `neo4j_graphrag` | **HIGH** — subtle interface contract violations cause silent failures |
| `agents/kg_pipeline_agent.py` | Pipeline agent — orchestrates extraction + entity resolution | **HIGH** — prompt template format is fragile |
| `services/llm_provider.py` | `AnthropicProvider` — all LLM calls flow through here | **MEDIUM** — changing the return type or error handling breaks all agents |
| `utils/pipeline_runner.py` | Web UI entry point — async/threading wrapper | **MEDIUM** — async model is precise and easy to break |
| `app.py` (lines ~427-481) | Streamlit UI for Step 6 | **LOW** — UI only, but file selection logic matters |
| `orchestrator.py` (lines ~206-233) | CLI entry point for Step 6 | **LOW** — simpler path, fewer moving parts |

---

## Invariant Checklist

### 1. `AnthropicLLM.__init__` MUST call `super().__init__()`

```python
# CORRECT
super().__init__(
    model_name=resolved_name,
    model_params=model_params or {},
    **kwargs,
)

# WRONG — missing super().__init__() causes missing _rate_limit_handler
self.model_name = model_name  # ← do NOT set attributes manually without super()
```

**Why:** `LLMInterface.__init__()` sets `self.model_name`, `self.model_params`, and `self._rate_limit_handler`. The pipeline and its internal components may access any of these. Without the super call, you get `AttributeError` at unpredictable points deep in the `neo4j_graphrag` pipeline DAG.

**Verify:** `hasattr(AnthropicLLM(...), '_rate_limit_handler')` must be `True`.

---

### 2. `AnthropicLLM.ainvoke` MUST use `asyncio.to_thread()`

```python
# CORRECT
async def ainvoke(self, input, ...):
    return await asyncio.to_thread(self.invoke, input, ...)

# WRONG — blocks the event loop, kills pipeline concurrency, can cause hangs
async def ainvoke(self, input, ...):
    return self.invoke(input, ...)
```

**Why:** `SimpleKGPipeline` runs chunk extractions via `asyncio.gather()`. A synchronous `ainvoke` blocks the event loop thread. With one chunk this appears to work but is still wrong; with multiple chunks it serializes everything; in edge cases it can deadlock.

---

### 3. `AnthropicLLM.invoke` MUST strip markdown code fences

```python
text = self._strip_markdown(text)  # before returning LLMResponse
```

**Why:** Claude wraps JSON in ` ```json ... ``` `. The pipeline's `json_repair` handles *some* cases, but not all. Without stripping, `LLMGenerationError("LLM response is not valid JSON")` is raised intermittently.

---

### 4. The prompt template MUST contain `{text}`, `{schema}`, `{examples}` placeholders

```python
# CORRECT — uses {text} etc as format placeholders
"Input text:\n{text}"

# WRONG — pre-formatted f-string, no placeholders for the pipeline to fill
f"Input text:\n{some_variable}"
```

**Why:** `LLMEntityRelationExtractor.extract_for_chunk()` calls:
```python
prompt = self.prompt_template.format(text=chunk.text, schema=..., examples=...)
```
Without `{text}`, the actual chunk text is never injected — the LLM gets a static prompt and extracts nothing useful.

**Extra rule:** Any literal `{` or `}` in the template (e.g. from baked-in context samples) must be escaped as `{{` / `}}` or Python's `str.format()` will raise `KeyError`/`ValueError`.

---

### 5. `PipelineRunner.run_kg_pipeline` MUST wrap `asyncio.run()` in a `ThreadPoolExecutor`

```python
# CORRECT
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    future = pool.submit(asyncio.run, agent.run_pipeline(files))
    future.result()

# WRONG — raises RuntimeError inside Streamlit's event loop
asyncio.run(agent.run_pipeline(files))
```

**Why:** Streamlit runs its own tornado event loop. `asyncio.run()` cannot be called from within a running event loop. The `ThreadPoolExecutor` creates a worker thread with its own fresh event loop.

**Note:** The CLI `orchestrator.py` calls `asyncio.run()` directly — this is fine because the CLI doesn't have a pre-existing event loop.

---

### 6. `SimpleKGPipeline` must be created with `on_error="RAISE"`

```python
# CORRECT
on_error="RAISE"

# WRONG — silently swallows all extraction and parse errors
on_error="IGNORE"
```

**Why:** With `"IGNORE"`, every failed chunk produces an empty graph silently. The pipeline appears to succeed but writes nothing. This was the original bug (B005) that made Step 6 appear broken.

---

### 7. `SentenceTransformerEmbedder.__init__` MUST call `super().__init__()`

```python
# CORRECT
super().__init__()

# WRONG
# (no super call)
```

**Why:** `Embedder.__init__()` sets `_rate_limit_handler`. Same pattern as the LLM adapter.

---

### 8. `schema="FREE"` is the correct schema mode

```python
# CORRECT
schema="FREE"

# WRONG — dict format is not accepted by SimpleKGPipeline
schema={"node_types": ["Product", ...], "additional_node_types": False}
```

**Why:** `SimpleKGPipeline` validates the `schema` parameter via pydantic. Accepted values are: `"FREE"` (empty schema, open extraction), `"EXTRACTED"` (LLM extracts schema first), a `GraphSchema` instance, or a dict matching `GraphSchema`'s shape. An arbitrary dict with non-matching keys causes a `PipelineDefinitionError`.

---

## Post-Merge Verification

Run these checks after merging into main. If any fail, the pipeline is broken.

### Quick smoke test (no API key needed)

```bash
python3 -c "
from services.anthropic_graphrag import AnthropicLLM, SentenceTransformerEmbedder

# 1. Check super().__init__() was called
import os; os.environ.setdefault('PROJECT_ANTHROPIC_API_KEY', 'dummy')
llm = AnthropicLLM(model_name='claude-haiku-4-5-20251001')
assert hasattr(llm, '_rate_limit_handler'), 'FAIL: missing _rate_limit_handler'

# 2. Check markdown stripping
assert AnthropicLLM._strip_markdown('\`\`\`json\n{\"a\":1}\n\`\`\`') == '{\"a\":1}', 'FAIL: markdown not stripped'

# 3. Check prompt template has {text}
from agents.kg_pipeline_agent import KgPipelineAgent
agent = KgPipelineAgent.__new__(KgPipelineAgent)
tmpl = agent._build_prompt_template('sample')
assert '{text}' in tmpl, 'FAIL: prompt missing {text}'
assert '{schema}' in tmpl, 'FAIL: prompt missing {schema}'
assert '{examples}' in tmpl, 'FAIL: prompt missing {examples}'

# 4. Check ainvoke uses to_thread
import inspect, asyncio
src = inspect.getsource(AnthropicLLM.ainvoke)
assert 'to_thread' in src, 'FAIL: ainvoke must use asyncio.to_thread'

# 5. Check on_error=RAISE in pipeline creation
src = inspect.getsource(KgPipelineAgent.run_pipeline)
assert 'on_error=\"RAISE\"' in src or \"on_error='RAISE'\" in src, 'FAIL: on_error must be RAISE'

print('All Step 6 invariants OK')
"
```

### Unit tests

```bash
python3 -m pytest tests/test_key_logic.py tests/test_pipeline_runner.py -v
```

### Full pipeline test (requires API key + Neo4j)

```bash
# From the web UI: run Step 6 with reviews.txt
# Expected console output includes ALL of these lines:
#   [debug] prompt_template length=..., has {text}=True
#   [debug] Creating SimpleKGPipeline...
#   [debug] Pipeline created OK
#   [debug] Running pipeline...
#   [loader] Loaded ... chars
#   [splitter] Split into N chunk(s)
#   ✓ Processed reviews.txt. Result: ...

# Check the debug log was written:
ls -la data/restaurant_data/debug/debug_llm_KgPipelineInfoExtractor.md
```

---

## Common Merge Conflict Scenarios

### You changed `services/llm_provider.py`

- Check that `AnthropicProvider.generate()` still returns `tuple[str, str]` (text, model_used).
- Check that it still accepts `log_file` as a kwarg (used for retry event logging).
- Check that `AnthropicProvider.DEFAULT_MODEL` still exists (used as fallback in `AnthropicLLM.__init__`).

### You changed `agents/schema_agent.py`

- `KgPipelineAgent` inherits `BaseAgent` from this file. If you changed `BaseAgent.__init__` signature, update `KgPipelineAgent.__init__` accordingly.

### You changed `services/graph_service.py`

- `KgPipelineAgent.__init__` reads `graphdb.driver`. If you changed the singleton pattern or the `.driver` property, the pipeline will get `None` and fail at Neo4j write time.

### You added a new LLM provider or adapter

- It MUST call `super().__init__(model_name, model_params)` on `LLMInterface`.
- Its `ainvoke` MUST use `asyncio.to_thread()` for any blocking I/O.
- It MUST strip markdown code fences from responses intended for JSON parsing.

### You changed `requirements.txt` / dependency versions

- `neo4j-graphrag` is pinned at 1.14.0. Version changes may alter `LLMInterface`, `Embedder`, `SimpleKGPipeline` signatures, or the internal pipeline DAG. Test Step 6 end-to-end after any upgrade.
- `sentence-transformers` model loading can break on Python version changes (the `embeddings.position_ids` UNEXPECTED warning is benign, but other warnings may not be).

---

## Architecture Diagram (for reference)

```
                    ┌─────────────────────┐
                    │  User clicks        │
                    │  "Run GraphRAG"     │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │  PipelineRunner      │
                    │  .run_kg_pipeline()  │
                    │                     │
                    │  ThreadPoolExecutor  │
                    │  └─ asyncio.run()   │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │  KgPipelineAgent     │
                    │  .run_pipeline()     │
                    │                     │
                    │  for each file:      │
                    │  ├─ sample context   │
                    │  ├─ build template   │
                    │  └─ SimpleKGPipeline │
                    └─────────┬───────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
  ┌──────▼──────┐   ┌────────▼────────┐   ┌──────▼──────┐
  │ Markdown    │   │ AnthropicLLM    │   │ Sentence    │
  │ DataLoader  │   │                 │   │ Transformer │
  │             │   │ .ainvoke()      │   │ Embedder    │
  │ reads file  │   │ → to_thread()   │   │             │
  │ → PdfDoc    │   │ → provider      │   │ local model │
  └─────────────┘   │   .generate()   │   │ 384-dim     │
                    │ → strip markdown│   └─────────────┘
                    │ → LLMResponse   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    Neo4j        │
                    │  Neo4jWriter    │
                    │  + resolver     │
                    └─────────────────┘
```
