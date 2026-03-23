# Bug Log

Tracks bugs found and fixed in this project. Format per global CLAUDE.md standard.

<!-- Template:
## B<id> · <short title>
**Date:** YYYY-MM-DD | **Regression:** <commit> | **Fix:** <commit or "this session">

**Root cause:** ...
**What went wrong:** ...
**What should have been done:** ...
**Test that would have caught it:**
```python
# minimal failing test
```
-->

---

## B001 · `app.py` IndentationError — `st.rerun()` misaligned
**Date:** 2026-03-23 | **Regression:** 5f5604c | **Fix:** this session

**Root cause:** `st.rerun()` was indented at 12 spaces inside the `with st.status(...)` block, but the block body used 16-space indent — Python could not resolve the indentation level.

**What went wrong:** The live-log streaming refactor (`5f5604c`) added extra indentation to the `with st.status` body without adjusting `st.rerun()` to match, producing a syntax error on load.

**What should have been done:** Consistent 4-space indent steps throughout the block; a syntax check (`python -m py_compile app.py`) before merging would have caught it immediately.

**Test that would have caught it:**
```python
import subprocess, sys
result = subprocess.run([sys.executable, "-m", "py_compile", "app.py"])
assert result.returncode == 0, "app.py has a syntax error"
```

---

## B002 · `IntentAgent` simulation mode skips `_generate()` — LLM log empty
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** `IntentAgent.refine_intent()` has its own simulation-mode heuristics that return early without calling `_generate()`, so `log_llm_interaction` is never reached.

**What went wrong:** `BaseAgent._generate()` handles both real and simulated calls and always logs. `IntentAgent` duplicated the simulation logic inline, bypassing the base class entirely, leaving the LLM Log expander permanently empty in the web UI.

**What should have been done:** Simulation fallbacks should live exclusively in `BaseAgent._generate()`. Agent subclasses should never branch on `self.provider is None` themselves.

**Test that would have caught it:**
```python
def test_intent_simulation_writes_log(tmp_path):
    agent = IntentAgent(data_dir=str(tmp_path))
    assert agent.provider is None  # no API key in test env
    agent.refine_intent("analyze restaurants")
    logs = list((tmp_path / "debug").glob("debug_llm_IntentAgent_*.md"))
    assert logs, "simulation mode must write a log entry"
```

---

## B003 · `schema_agent.py` missing `import time` — NameError at runtime
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** `time.sleep(1)` was called inside `SchemaRefinementLoop` but `import time` was never added to the file.

**What went wrong:** The sleep call was added to pace LLM iterations but the import was omitted. The error only surfaces when the critic rejects a proposal and a revision cycle runs, so it wasn't caught in simple smoke tests.

**What should have been done:** Any use of a stdlib module must have a corresponding import. `ruff check` would have flagged this as `F821 undefined name`.

**Test that would have caught it:**
```python
def test_schema_agent_importable():
    from agents.schema_agent import SchemaRefinementLoop  # noqa: F401
```

---

## B004 · `PipelineRunner` never starts Neo4j — graph stages silently fail
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** The CLI `Orchestrator.__init__` calls `ContainerService.start_container()` on startup, but `PipelineRunner` (used by the web UI) had no equivalent, so graph stages would fail or hang with no clear error.

**What went wrong:** `run_graph_build` and `run_kg_pipeline` both connect to Neo4j without first ensuring the container is running. The web UI gave no feedback — the KG pipeline stage produced no output at all.

**What should have been done:** Any entry point that drives graph stages must call `ContainerService.start_container()` (idempotent) before proceeding. `PipelineRunner` needed an `ensure_neo4j()` method called at the top of both graph stages.

**Test that would have caught it:**
```python
def test_run_graph_build_starts_neo4j(mocker):
    mock_start = mocker.patch("services.container_service.ContainerService.start_container")
    mocker.patch("agents.graph_builder.GraphBuilderAgent.build_graph", return_value=True)
    runner = PipelineRunner(context=fake_ctx())
    runner.run_graph_build()
    mock_start.assert_called_once()
```

---

## B005 · `SimpleKGPipeline` wrong schema format + silent error suppression
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** `KgPipelineAgent` passed `{"node_types": [...], "additional_node_types": False}` as the schema, which does not match the `SimpleKGPipeline` API. The default `on_error='IGNORE'` then suppressed all resulting failures silently.

**What went wrong:** With an unrecognised schema dict and `on_error='IGNORE'`, every extraction step failed quietly — no graph nodes were written, no log output appeared, and no error was shown to the user.

**What should have been done:** Use `schema='FREE'` for open-ended extraction, or validate against `GraphSchema`. Always set `on_error='RAISE'` during development so failures surface immediately.

**Test that would have caught it:**
```python
def test_kg_pipeline_on_error_is_raise():
    import inspect
    from agents.kg_pipeline_agent import KgPipelineAgent
    src = inspect.getsource(KgPipelineAgent.run_pipeline)
    assert "on_error=\"RAISE\"" in src, "pipeline must not silently suppress errors"
```

---

## B006 · Retry backoff too short — rate-limit retries exhausted under slow LLMs
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** `AnthropicProvider.generate()` used `2^attempt + random` seconds backoff (max ~4s after 3 attempts) — too short for Anthropic rate-limit windows, especially with slower models.

**What went wrong:** Under sustained load the retry window expired before the rate limit cleared, raising `RuntimeError` to the user. Retry events also weren't written to the debug log, making diagnosis difficult.

**What should have been done:** Use `15 * 2^attempt` seconds with at least 5 retries (~15s, 30s, 60s, 120s, 240s). Log each retry event so they appear in the UI debug panel.

**Test that would have caught it:**
```python
def test_retry_backoff_is_sufficient():
    waits = [15 * (2 ** i) for i in range(5)]
    assert min(waits) >= 15, "minimum backoff must be at least 15s"
    assert all(waits[i] < waits[i + 1] for i in range(len(waits) - 1))
```

---

## B007 · `run_kg_pipeline` silently swallows `RuntimeError` from `asyncio.run()`
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** Streamlit runs its own async event loop (tornado). Calling `asyncio.run()` inside an already-running loop raises `RuntimeError: This event loop is already running`, which was immediately caught by `except Exception: return False` with no logging.

**What went wrong:** The bare `except Exception: return False` pattern hid the real error entirely — the UI showed no output, no error message, and no debug log entries because the pipeline never executed.

**What should have been done:** Run async pipelines in a `ThreadPoolExecutor` worker so `asyncio.run()` creates a fresh event loop in its own thread, independent of Streamlit's loop. Never use bare `except Exception` without at least logging the error.

**Test that would have caught it:**
```python
def test_run_kg_pipeline_surfaces_exceptions(mocker):
    mocker.patch("services.container_service.ContainerService.start_container")
    mocker.patch("agents.kg_pipeline_agent.KgPipelineAgent.run_pipeline",
                 side_effect=RuntimeError("boom"))
    runner = PipelineRunner(context=fake_ctx())
    with pytest.raises(RuntimeError, match="boom"):
        runner.run_kg_pipeline(["reviews.txt"])
```

---

## B008 · `AnthropicLLM` missing `super().__init__()` — pipeline unstable
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** `AnthropicLLM.__init__` never called `LLMInterface.__init__()`, so `_rate_limit_handler` was missing. The `ainvoke` method also ran synchronous HTTP I/O directly in the async event loop instead of using `asyncio.to_thread()`.

**What went wrong:** The pipeline could fail with `AttributeError` for `_rate_limit_handler`, and the blocking synchronous call in `ainvoke` starved the async event loop, causing hangs or degraded performance.

**What should have been done:** Always call `super().__init__()` when subclassing framework interfaces. Mirror the working `GeminiLLM` pattern: call `super().__init__(model_name, model_params)` and use `asyncio.to_thread()` in `ainvoke`.

**Test that would have caught it:**
```python
def test_anthropic_llm_has_rate_limit_handler():
    from services.anthropic_graphrag import AnthropicLLM
    llm = AnthropicLLM(model_name="test")
    assert hasattr(llm, '_rate_limit_handler')
```

---

## B009 · `KgPipelineAgent` prompt template missing `{text}` placeholder
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** `_contextualize_prompt()` returned a pre-formatted f-string with no `{text}` placeholder. The neo4j_graphrag pipeline calls `template.format(text=chunk.text, schema=..., examples=...)` — without `{text}`, the actual chunk text was never injected into the LLM prompt.

**What went wrong:** The LLM received a static prompt with only a context sample, never the actual text chunk to extract from. Combined with other issues, the pipeline produced no useful output.

**What should have been done:** The prompt template must contain `{text}`, `{schema}`, and `{examples}` placeholders matching what `PromptTemplate.format()` injects. Any literal braces in the template must be escaped as `{{` / `}}`.

**Test that would have caught it:**
```python
def test_prompt_template_has_text_placeholder():
    from agents.kg_pipeline_agent import KgPipelineAgent
    agent = KgPipelineAgent.__new__(KgPipelineAgent)
    template = agent._build_prompt_template("sample context")
    assert "{text}" in template, "prompt must have {text} for chunk injection"
```

---

## B010 · `AnthropicLLM` doesn't strip markdown code fences from response
**Date:** 2026-03-23 | **Regression:** ea217a3 | **Fix:** this session

**Root cause:** Claude wraps JSON responses in ` ```json ... ``` ` code blocks. The `GeminiLLM` adapter strips these, but `AnthropicLLM` returned raw text. While `json_repair` sometimes handles this, inconsistent responses caused JSON parse failures.

**What went wrong:** The pipeline's JSON parser received markdown-wrapped JSON, sometimes failing to parse it, triggering `LLMGenerationError` with `on_error="RAISE"`.

**What should have been done:** Strip markdown code fences in the LLM adapter before returning, same as the Gemini adapter.

**Test that would have caught it:**
```python
def test_anthropic_llm_strips_markdown():
    from services.anthropic_graphrag import AnthropicLLM
    result = AnthropicLLM._strip_markdown('```json\n{"nodes": []}\n```')
    assert result == '{"nodes": []}'
```
