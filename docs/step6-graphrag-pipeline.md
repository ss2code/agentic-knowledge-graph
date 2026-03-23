# Step 6 — GraphRAG Pipeline: Architecture, Design & Code Reference

> **Status:** Working as of 2026-03-23 (main branch).
> This document covers the unstructured-text knowledge-graph extraction pipeline.

---

## 1. Purpose

Step 6 takes **unstructured text files** (`.txt`, `.md`) from `<context>/user_data/`, runs them through an LLM-powered entity/relationship extractor, and writes the resulting knowledge graph into Neo4j. It complements Step 5 (structured graph build from `construction_plan.json`) by handling free-form text that doesn't fit a pre-defined schema.

The pipeline also performs **entity resolution** — linking the `__Entity__` nodes created by the extractor back to domain nodes already in the graph (from Step 5) using Jaro-Winkler string similarity.

---

## 2. Component Map

```
Entry points
─────────────
  CLI:  orchestrator.py  → Orchestrator.run_kg_pipeline()
  Web:  app.py (Step 6)  → PipelineRunner.run_kg_pipeline()

Both call
─────────
  agents/kg_pipeline_agent.py  → KgPipelineAgent
    ├── .run_pipeline(file_names)      # async — LLM extraction + Neo4j write
    ├── .resolve_entities()            # sync  — Jaro-Winkler entity linking
    └── .log_extraction_stats()        # sync  — append to graph_build_log.md

LLM + Embedding adapters
─────────────────────────
  services/anthropic_graphrag.py
    ├── AnthropicLLM          (implements neo4j_graphrag LLMInterface)
    └── SentenceTransformerEmbedder  (implements neo4j_graphrag Embedder)

LLM provider
────────────
  services/llm_provider.py → AnthropicProvider
    └── .generate(prompt, model, system_instruction, log_file)

External library
────────────────
  neo4j_graphrag v1.14.0
    └── SimpleKGPipeline  (orchestrates the internal DAG)
```

---

## 3. Data Flow (per file)

```
┌──────────────────────────────────────────────────────────────────────┐
│  SimpleKGPipeline internal DAG                                       │
│                                                                      │
│  MarkdownDataLoader ──► RegexTextSplitter ──► TextChunkEmbedder      │
│        │                       │                     │               │
│        │ (document_info)       │ (chunks)             │ (embedded)   │
│        │                       │                     │               │
│        └──────────┬────────────┘                     │               │
│                   │                                  │               │
│            SchemaBuilder (FREE = empty)               │               │
│                   │ (schema)                         │               │
│                   └───────────┬───────────────────────┘               │
│                               ▼                                      │
│                 LLMEntityRelationExtractor                            │
│                   │  (calls AnthropicLLM.ainvoke per chunk)           │
│                   │  prompt = template.format(text=chunk, schema=...) │
│                   ▼                                                  │
│              GraphPruning                                            │
│                   ▼                                                  │
│              Neo4jWriter  ──► writes nodes/rels to Neo4j             │
│                   ▼                                                  │
│         SinglePropertyExactMatchResolver                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

After pipeline completes:
  KgPipelineAgent.resolve_entities()   ← Jaro-Winkler cross-linking
  KgPipelineAgent.log_extraction_stats() ← append to debug/graph_build_log.md
```

---

## 4. Key Classes — Detailed

### 4.1 `KgPipelineAgent` (`agents/kg_pipeline_agent.py`)

Inherits `BaseAgent`. Owns the full lifecycle of the GraphRAG step.

| Method | Type | Purpose |
|--------|------|---------|
| `__init__(api_key, data_dir, model_name)` | sync | Creates `AnthropicLLM` adapter, `SentenceTransformerEmbedder`, grabs `graphdb.driver` |
| `_build_prompt_template(context_sample)` | sync | Returns a prompt string with `{text}`, `{schema}`, `{examples}` placeholders |
| `_get_representative_sample(file_path)` | sync | Reads up to 3000 chars; samples large files |
| `run_pipeline(file_names)` | **async** | Per-file: build prompt, create `SimpleKGPipeline`, call `run_async` |
| `resolve_entities()` | sync | Jaro-Winkler matching of `__Entity__` nodes to domain nodes |
| `log_extraction_stats()` | sync | Writes entity summary to `debug/graph_build_log.md` |

### 4.2 `AnthropicLLM` (`services/anthropic_graphrag.py`)

Implements `neo4j_graphrag.llm.LLMInterface` — the contract the `SimpleKGPipeline` uses to call the LLM.

**Critical implementation requirements:**

1. **`super().__init__(model_name, model_params)` MUST be called.** The base class sets `_rate_limit_handler` and other attributes the pipeline reads.

2. **`ainvoke` MUST use `asyncio.to_thread(self.invoke, ...)`**, not a direct synchronous call. The pipeline runs an async DAG with `asyncio.gather` — a blocking HTTP call inside `ainvoke` starves the event loop.

3. **`_strip_markdown`** must be applied to the response before returning. Claude wraps JSON in ` ```json ... ``` ` code blocks; the pipeline's JSON parser (`json_repair`) can handle some cases but not all.

### 4.3 `SentenceTransformerEmbedder` (`services/anthropic_graphrag.py`)

Wraps `sentence-transformers/all-MiniLM-L6-v2` (384-dim) for local embeddings.

Calls `super().__init__()` on `neo4j_graphrag.embeddings.base.Embedder` — this sets `_rate_limit_handler`. The base class provides a default `async_embed_query` that calls `embed_query` synchronously.

### 4.4 Custom Pipeline Components

| Class | Base | Purpose |
|-------|------|---------|
| `MarkdownDataLoader` | `neo4j_graphrag...DataLoader` | Reads any text file (not just PDF); extracts `# Title` as document title |
| `RegexTextSplitter` | `neo4j_graphrag...TextSplitter` | Splits text on a regex pattern (default `\n---\n`); files without the delimiter become a single chunk |

---

## 5. The Prompt Template Contract

The `SimpleKGPipeline` passes the prompt template to `LLMEntityRelationExtractor`, which wraps string templates in a `PromptTemplate` object. At extraction time it calls:

```python
prompt = self.prompt_template.format(
    text=chunk.text,           # the actual chunk being extracted
    schema=schema.model_dump(),  # dict of allowed node/rel types
    examples=examples,         # few-shot examples (usually "")
)
```

**The template string MUST contain `{text}`, `{schema}`, and `{examples}` as Python format placeholders.**

If the template contains any literal braces (e.g. from baked-in context text), they must be escaped as `{{` / `}}`.

Current template structure in `_build_prompt_template`:
```
[system instruction]
[domain context from file sample — braces escaped]
Schema guidance:
{schema}
Examples:
{examples}
Input text:
{text}
```

---

## 6. Async Execution Model

```
Streamlit event loop (tornado)
  │
  └─ PipelineRunner.run_kg_pipeline(files)
       │
       └─ ThreadPoolExecutor(max_workers=1)
            │
            └─ asyncio.run(agent.run_pipeline(files))   ← fresh event loop in worker thread
                 │
                 └─ await SimpleKGPipeline.run_async()
                      │
                      ├─ MarkdownDataLoader.run()         (sync file I/O, but wrapped async)
                      ├─ RegexTextSplitter.run()           (pure CPU)
                      ├─ TextChunkEmbedder.run()           (sync model inference per chunk)
                      ├─ SchemaBuilder.run()               (pure CPU)
                      ├─ LLMEntityRelationExtractor.run()
                      │    └─ asyncio.gather(*[per-chunk tasks])
                      │         └─ AnthropicLLM.ainvoke()  ← asyncio.to_thread(invoke)
                      ├─ GraphPruning.run()                (pure CPU)
                      ├─ Neo4jWriter.run()                 (sync Bolt driver calls)
                      └─ SinglePropertyExactMatchResolver   (sync Bolt driver calls)
```

**Why `ThreadPoolExecutor`?** Streamlit runs its own tornado event loop. Calling `asyncio.run()` from within an already-running loop raises `RuntimeError`. The worker thread creates a fresh, independent event loop.

**Why `asyncio.to_thread` in `ainvoke`?** The pipeline's `asyncio.gather` runs chunk extractions concurrently (up to `max_concurrency=5`). If `ainvoke` blocks synchronously, it starves the event loop and all concurrency collapses. `to_thread` releases the event loop while the HTTP call runs in a thread pool.

---

## 7. Error Handling

| Layer | Strategy |
|-------|----------|
| `SimpleKGPipeline` | `on_error="RAISE"` — extraction/parse errors propagate immediately |
| `KgPipelineAgent.run_pipeline` | `try/except Exception` with `traceback.print_exc()` per file |
| `PipelineRunner.run_kg_pipeline` | `future.result()` re-raises from the worker thread |
| `app.py` (web) | `try/except` with `st.error()` display |
| `orchestrator.py` (CLI) | `try/except` with colored terminal output |
| `AnthropicProvider.generate` | Retries 5x on `RateLimitError` with exponential backoff (15s base) |

---

## 8. Debug Artifacts

| File | Written by | Content |
|------|-----------|---------|
| `<context>/debug/debug_llm_KgPipelineInfoExtractor.md` | `AnthropicLLM.invoke` via `log_llm_interaction` | Full prompt + response for every LLM call |
| `<context>/debug/graph_build_log.md` | `KgPipelineAgent.log_extraction_stats` | Summary of all `__Entity__` nodes extracted |
| Console `[debug]` / `[loader]` / `[splitter]` lines | `KgPipelineAgent.run_pipeline`, component classes | Stage-by-stage progress trace |

---

## 9. Neo4j Graph Schema (output)

The pipeline creates nodes with a `__Entity__` label (neo4j_graphrag convention) plus domain labels assigned by the LLM (e.g. `Product`, `Ingredient`). Relationships are typed by the LLM (e.g. `MENTIONS`, `PART_OF`).

After pipeline completion, `resolve_entities()` creates `CORRESPONDS_TO` relationships between `__Entity__` nodes and domain nodes from Step 5, using Jaro-Winkler similarity on the `name` property (threshold 0.85).

The entity resolution requires **APOC** to be installed in Neo4j for `apoc.text.jaroWinklerDistance`.

---

## 10. Dependencies

| Package | Version | Role |
|---------|---------|------|
| `neo4j-graphrag` | 1.14.0 | `SimpleKGPipeline`, `LLMInterface`, `Embedder`, all internal components |
| `anthropic` | (latest) | Anthropic Messages API via `AnthropicProvider` |
| `sentence-transformers` | (latest) | Local embeddings via `all-MiniLM-L6-v2` |
| `json-repair` | (transitive) | Fixes malformed JSON from LLM responses |
| `neo4j` | (transitive) | Bolt driver for graph writes |

**Environment variables:**
- `PROJECT_ANTHROPIC_API_KEY` — required; without it `AnthropicProvider.__init__` raises `ValueError`
- `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` — used by `graphdb` singleton

---

## 11. Known Fragilities & Past Bugs

| ID | Issue | How it was fixed | What to watch |
|----|-------|-----------------|---------------|
| B005 | Wrong schema format + silent `on_error='IGNORE'` | Use `schema="FREE"`, set `on_error="RAISE"` | Never change `on_error` back to `"IGNORE"` during dev |
| B007 | `asyncio.run()` inside Streamlit's event loop | `ThreadPoolExecutor` wrapping | Any new caller of `run_pipeline` from an async context must use the same pattern |
| B008 | Missing `super().__init__()` in `AnthropicLLM` | Added the call | Any new `LLMInterface` subclass must call `super().__init__()` |
| B009 | Prompt template missing `{text}` placeholder | `_build_prompt_template` with proper placeholders | Never use pre-formatted f-strings as `prompt_template` |
| B010 | No markdown stripping on Anthropic responses | `_strip_markdown()` in `AnthropicLLM.invoke` | Any new LLM adapter must strip code fences |

See `docs/bugs.md` for full details on each.
