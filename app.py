"""
app.py — Streamlit entry point for the KG Orchestrator web UI.
"""

import os
import glob

import streamlit as st
import streamlit.components.v1 as components

from core.context import Context
from utils.context_scanner import (
    scan_contexts,
    load_artifact,
    load_llm_logs,
    get_last_run_time,
    load_graph_build_log,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(layout="wide", page_title="KG Orchestrator")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    return st.session_state.get("api_key") or os.getenv("GEMINI_API_KEY", "")


def make_runner(ctx: Context):
    from utils.pipeline_runner import PipelineRunner
    return PipelineRunner(context=ctx, api_key=get_api_key())


def status_badge(label: str, value) -> str:
    """Return a coloured markdown badge string."""
    color_map = {
        "VALID": "green", "BUILT": "green", "COMPLETE": "green",
        "STALE": "orange", "PENDING": "gray",
        True: "green", False: "gray",
    }
    color = color_map.get(value, "gray")
    display = str(value) if not isinstance(value, bool) else ("Yes" if value else "No")
    return f":{color}[{label}: **{display}**]"


def clear_extraction_state():
    """Clear all extraction session keys (e.g. after saving the plan)."""
    for k in ("extraction_proposed_entities", "extraction_entities_approved",
              "extraction_proposed_facts", "extraction_rerun_requested"):
        st.session_state.pop(k, None)


def reset_extraction_state():
    """Reset extraction state and flag that a re-run was requested."""
    clear_extraction_state()
    st.session_state["extraction_rerun_requested"] = True


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("KG Orchestrator")

    # API key
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        value=st.session_state.get("api_key", ""),
        placeholder="Paste key or set GEMINI_API_KEY env var",
    )
    if api_key_input:
        st.session_state["api_key"] = api_key_input

    st.divider()

    # Context selector
    contexts = scan_contexts("data")
    context_names = [c["name"] for c in contexts]

    st.subheader("Project Context")

    selected_name = st.selectbox(
        "Select context",
        options=context_names,
        index=0 if context_names else None,
        placeholder="No contexts found",
    )

    # Track context switches so we can reset extraction state
    if st.session_state.get("_active_context") != selected_name:
        st.session_state["_active_context"] = selected_name
        clear_extraction_state()

    # New context creation
    with st.expander("+ New Context"):
        new_name = st.text_input("Context name", key="new_ctx_name")
        if st.button("Create", key="create_ctx_btn"):
            if new_name.strip():
                new_path = os.path.join("data", new_name.strip())
                new_ctx = Context.from_path(new_path)
                new_ctx.ensure_directories()
                st.success(f"Created context '{new_name.strip()}'")
                st.rerun()
            else:
                st.warning("Enter a name first.")

    st.divider()

    # Status panel
    if selected_name:
        selected = next((c for c in contexts if c["name"] == selected_name), None)
        if selected and selected.get("state"):
            state = selected["state"]
            st.subheader("Status")
            st.markdown(status_badge("Intent", state.get("intent_defined", False)))
            st.markdown(status_badge("Files", state.get("files_approved", False)))
            st.markdown(status_badge("Schema", state.get("schema_status", "PENDING")))
            st.markdown(status_badge("Graph", state.get("graph_status", "PENDING")))
            if state.get("graphrag_status"):
                st.markdown(status_badge("GraphRAG", state.get("graphrag_status")))
            if state.get("last_updated"):
                st.caption(f"Updated: {state['last_updated'][:16]}")
        else:
            st.info("No state file yet.")

# ---------------------------------------------------------------------------
# Main content — guard against no contexts
# ---------------------------------------------------------------------------

if not context_names or not selected_name:
    st.info(
        "No project contexts found. Create one in the sidebar by clicking **+ New Context** "
        "and entering a name. Then add your data files to `data/<name>/user_data/`."
    )
    st.stop()

selected = next(c for c in contexts if c["name"] == selected_name)
ctx = Context.from_path(selected["path"])

st.header(f"Context: {ctx.name}")

# ---------------------------------------------------------------------------
# Step 1 — Intent Definition
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("① Intent Definition")
    col2.caption(f"Last run: {get_last_run_time(ctx.debug_dir, 'IntentAgent') or 'never'}")

    if intent := load_artifact(ctx.base_path, "user_intent.json"):
        st.json(intent)

    goal = st.text_area(
        "Describe your knowledge graph goal",
        key="intent_goal",
        placeholder="e.g. Build a graph of restaurant menus with dishes, ingredients, and prices.",
    )
    if st.button("▶ Run Intent Refinement", key="run_intent"):
        if not get_api_key():
            st.error("Set a Gemini API key in the sidebar first.")
        else:
            try:
                with st.spinner("Calling Gemini..."):
                    make_runner(ctx).run_intent(goal)
                st.rerun()
            except Exception as e:
                st.error(f"Intent agent failed: {e}")

    logs = load_llm_logs(ctx.debug_dir, agent_prefix="IntentAgent")
    with st.expander(f"LLM Log — IntentAgent ({len(logs)} interactions)"):
        for log in logs:
            st.markdown(log["content"])

# ---------------------------------------------------------------------------
# Step 2 — Data Ingestion
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("② Data Ingestion")
    col2.caption("")

    # --- Directory selector ---
    default_scan_dir = ctx.data_dir
    scan_dir = st.text_input(
        "Directory to scan",
        value=default_scan_dir,
        key="ingest_scan_dir",
        help="Absolute or relative path containing CSV, MD, or TXT files",
    )

    # Discover supported files in the chosen directory
    SUPPORTED_EXT = {".csv", ".md", ".txt", ".json"}
    discovered = []
    scan_dir_abs = os.path.abspath(scan_dir) if scan_dir else ""
    if scan_dir_abs and os.path.isdir(scan_dir_abs):
        discovered = sorted(
            f for f in os.listdir(scan_dir_abs)
            if not f.startswith(".")
            and os.path.splitext(f)[1].lower() in SUPPORTED_EXT
        )

    # --- File multiselect (explicit user choice required) ---
    selected_files = st.multiselect(
        f"Select files to approve ({len(discovered)} found)",
        options=discovered,
        default=[],
        key="ingest_selected_files",
        placeholder="Choose files…" if discovered else "No supported files found in directory",
    )

    selected_paths = [os.path.join(scan_dir_abs, f) for f in selected_files]

    # --- Approve button (active only when files are selected) ---
    approve_disabled = len(selected_paths) == 0
    btn_label = "Approve Selected Files" if approve_disabled else f"✅ Approve {len(selected_paths)} File(s)"
    if st.button(btn_label, key="approve_files", disabled=approve_disabled, type="primary"):
        try:
            with st.spinner("Saving approval..."):
                make_runner(ctx).approve_files(selected_paths=selected_paths)
            st.rerun()
        except Exception as e:
            st.error(f"File approval failed: {e}")

    # --- Compact approved-files display ---
    if approved := load_artifact(ctx.base_path, "approved_files.json"):
        approved_list = approved.get("files", [])
        if approved_list:
            st.success(
                f"**{len(approved_list)} approved:** "
                + "  ·  ".join(os.path.basename(p) for p in approved_list)
            )

# ---------------------------------------------------------------------------
# Step 3 — Schema Design
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("③ Schema Design")
    col2.caption(f"Last run: {get_last_run_time(ctx.debug_dir, 'SchemaRefinement') or 'never'}")

    if plan := load_artifact(ctx.base_path, "construction_plan.json"):
        st.json(plan)

    if st.button("▶ Run Schema Negotiation", key="run_schema"):
        if not get_api_key():
            st.error("Set a Gemini API key in the sidebar first.")
        else:
            try:
                with st.spinner("Negotiating schema with Gemini..."):
                    result = make_runner(ctx).run_schema_negotiation()
                st.rerun()
            except Exception as e:
                st.error(f"Schema negotiation failed: {e}")

    logs = load_llm_logs(ctx.debug_dir, agent_prefix="SchemaRefinement")
    with st.expander(f"LLM Log — SchemaRefinement ({len(logs)} interactions)"):
        for log in logs:
            st.markdown(log["content"])

# ---------------------------------------------------------------------------
# Step 4 — Extraction Design (multi-step Approve/Retry)
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("④ Extraction Design")
    col2.caption(f"Last run: {get_last_run_time(ctx.debug_dir, 'NERAgent') or 'never'}")

    existing_plan = load_artifact(ctx.base_path, "extraction_plan.json")

    if (existing_plan
            and not st.session_state.get("extraction_proposed_entities")
            and not st.session_state.get("extraction_rerun_requested")):
        # Show existing plan with option to re-run
        st.write("**Current extraction plan:**")
        st.json(existing_plan)
        if st.button("🔄 Re-run Extraction Design", key="rerun_extraction"):
            reset_extraction_state()
            st.rerun()
    else:
        # Multi-step flow
        proposed_entities = st.session_state.get("extraction_proposed_entities")
        entities_approved = st.session_state.get("extraction_entities_approved", False)
        proposed_facts = st.session_state.get("extraction_proposed_facts")

        # Step 4.1 — Propose entities
        if not proposed_entities:
            if st.button("▶ Propose Entities", key="propose_entities"):
                if not get_api_key():
                    st.error("Set a Gemini API key in the sidebar first.")
                else:
                    try:
                        with st.spinner("Proposing entity types..."):
                            result = make_runner(ctx).propose_entities()
                        st.session_state["extraction_proposed_entities"] = result
                        st.rerun()
                    except Exception as e:
                        st.error(f"Entity proposal failed: {e}")

        # Step 4.2 — Review proposed entities
        elif proposed_entities and not entities_approved:
            st.write("**Proposed entities:**")
            st.json(proposed_entities)
            col_a, col_b = st.columns(2)
            if col_a.button("✅ Approve Entities", key="approve_entities"):
                st.session_state["extraction_entities_approved"] = True
                st.rerun()
            if col_b.button("🔁 Retry Entities", key="retry_entities"):
                st.session_state.pop("extraction_proposed_entities", None)
                st.rerun()

        # Step 4.3 — Propose facts
        elif entities_approved and not proposed_facts:
            entities_list = proposed_entities if isinstance(proposed_entities, list) else []
            if isinstance(proposed_entities, dict):
                entities_list = proposed_entities.get("entities", [])
            if st.button("▶ Propose Facts", key="propose_facts"):
                if not get_api_key():
                    st.error("Set a Gemini API key in the sidebar first.")
                else:
                    try:
                        with st.spinner("Proposing fact types..."):
                            result = make_runner(ctx).propose_facts(entities_list)
                        st.session_state["extraction_proposed_facts"] = result
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fact proposal failed: {e}")

        # Step 4.4 — Review proposed facts and save
        elif proposed_facts:
            st.write("**Proposed facts:**")
            st.json(proposed_facts)
            feedback = st.text_input("Optional feedback for refinement", key="facts_feedback")
            col_a, col_b = st.columns(2)
            if col_a.button("✅ Save Plan", key="save_extraction_plan"):
                if not get_api_key():
                    st.error("Set a Gemini API key in the sidebar first.")
                else:
                    try:
                        entities_list = proposed_entities if isinstance(proposed_entities, list) else []
                        if isinstance(proposed_entities, dict):
                            entities_list = proposed_entities.get("entities", [])
                        facts_list = proposed_facts if isinstance(proposed_facts, list) else []
                        if isinstance(proposed_facts, dict):
                            facts_list = proposed_facts.get("facts", [])
                        with st.spinner("Saving extraction plan..."):
                            make_runner(ctx).save_extraction_plan(
                                entities_list, facts_list, model="gemini-2.0-flash"
                            )
                        clear_extraction_state()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Saving extraction plan failed: {e}")
            if col_b.button("🔁 Retry Facts", key="retry_facts"):
                st.session_state.pop("extraction_proposed_facts", None)
                st.rerun()

    logs = load_llm_logs(ctx.debug_dir, agent_prefix="NERAgent")
    with st.expander(f"LLM Log — NERAgent ({len(logs)} interactions)"):
        for log in logs:
            st.markdown(log["content"])

# ---------------------------------------------------------------------------
# Step 5 — Graph Build
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("⑤ Graph Build")
    col2.caption(f"Last run: {get_last_run_time(ctx.debug_dir, 'GraphBuilderAgent') or 'never'}")

    graph_log = load_graph_build_log(ctx.debug_dir)
    if graph_log:
        with st.expander("Graph build log"):
            st.markdown(graph_log)

    if st.button("▶ Run Graph Build", key="run_graph_build"):
        if not get_api_key():
            st.error("Set a Gemini API key in the sidebar first.")
        else:
            try:
                with st.spinner("Building graph in Neo4j..."):
                    success = make_runner(ctx).run_graph_build()
                if success:
                    st.success("Graph built successfully.")
                else:
                    st.warning("Graph build completed with warnings.")
                st.rerun()
            except Exception as e:
                st.error(f"Graph build failed: {e}")

    logs = load_llm_logs(ctx.debug_dir, agent_prefix="GraphBuilderAgent")
    with st.expander(f"LLM Log — GraphBuilderAgent ({len(logs)} interactions)"):
        for log in logs:
            st.markdown(log["content"])

# ---------------------------------------------------------------------------
# Step 6 — GraphRAG Pipeline
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("⑥ GraphRAG Pipeline")
    col2.caption(f"Last run: {get_last_run_time(ctx.debug_dir, 'KgPipelineInfoExtractor') or 'never'}")

    # File selector for unstructured text files
    txt_files = []
    if os.path.isdir(ctx.data_dir):
        txt_files = [
            os.path.join(ctx.data_dir, f)
            for f in os.listdir(ctx.data_dir)
            if f.lower().endswith((".txt", ".md")) and not f.startswith(".")
        ]

    if txt_files:
        selected_files = st.multiselect(
            "Select text files for GraphRAG pipeline",
            options=txt_files,
            default=txt_files,
            format_func=os.path.basename,
            key="graphrag_files",
        )
    else:
        selected_files = []
        st.info("No .txt or .md files found in user_data/.")

    if st.button("▶ Run GraphRAG Pipeline", key="run_kg_pipeline"):
        if not get_api_key():
            st.error("Set a Gemini API key in the sidebar first.")
        elif not selected_files:
            st.warning("Select at least one file.")
        else:
            try:
                with st.spinner("Running KG pipeline..."):
                    success = make_runner(ctx).run_kg_pipeline(selected_files)
                if success:
                    st.success("GraphRAG pipeline completed.")
                else:
                    st.error("GraphRAG pipeline failed.")
                st.rerun()
            except Exception as e:
                st.error(f"GraphRAG pipeline failed: {e}")

    logs = load_llm_logs(ctx.debug_dir, agent_prefix="KgPipelineInfoExtractor")
    with st.expander(f"LLM Log — KgPipelineInfoExtractor ({len(logs)} interactions)"):
        for log in logs:
            st.markdown(log["content"])

# ---------------------------------------------------------------------------
# Step 7 — Inspect Graph
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("⑦ Inspect Graph")
    col2.caption("")

    if st.button("🔍 Refresh Stats", key="inspect_graph"):
        try:
            from services.graph_service import graphdb

            count_result = graphdb.send_query("MATCH (n) RETURN count(n) as c")
            node_count = count_result[0]["c"] if count_result else 0
            st.metric("Total Nodes", node_count)

            label_result = graphdb.send_query(
                "MATCH (n) RETURN labels(n)[0] as label, count(n) as c ORDER BY c DESC"
            )
            if label_result:
                st.write("**Nodes by label:**")
                st.dataframe(label_result)
            else:
                st.info("No nodes found in the graph.")
        except Exception as e:
            st.warning(f"Neo4j not connected: {e}")

# ---------------------------------------------------------------------------
# Step 8 — Visualize
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("⑧ Visualize")
    col2.caption("")

    html_path = os.path.join(ctx.output_dir, "schema_viz.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as fh:
            html_content = fh.read()
        components.html(html_content, height=600, scrolling=True)

    if st.button("▶ Run Visualization", key="run_viz"):
        if not get_api_key():
            st.error("Set a Gemini API key in the sidebar first.")
        else:
            try:
                with st.spinner("Generating visualization..."):
                    path = make_runner(ctx).run_visualization()
                st.success(f"Visualization saved to {path}")
                st.rerun()
            except Exception as e:
                st.error(f"Visualization failed: {e}")

# ---------------------------------------------------------------------------
# Step 9 — Text-to-Cypher
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("⑨ Text-to-Cypher")
    col2.caption(f"Last run: {get_last_run_time(ctx.debug_dir, 'TextToCypherAgent') or 'never'}")

    nl_query = st.text_input(
        "Natural language query",
        key="nl_query",
        placeholder="e.g. Show all dishes with price under $15",
    )
    if st.button("▶ Translate & Run", key="run_t2c"):
        if not get_api_key():
            st.error("Set a Gemini API key in the sidebar first.")
        elif not nl_query.strip():
            st.warning("Enter a query first.")
        else:
            try:
                with st.spinner("Generating and running Cypher..."):
                    cypher, results = make_runner(ctx).run_text_to_cypher(nl_query)
                st.code(cypher, language="cypher")
                if results:
                    st.dataframe(results)
                else:
                    st.info("Query returned no results.")
            except Exception as e:
                st.error(f"Text-to-Cypher failed: {e}")

    logs = load_llm_logs(ctx.debug_dir, agent_prefix="TextToCypherAgent")
    with st.expander(f"LLM Log — TextToCypherAgent ({len(logs)} interactions)"):
        for log in logs:
            st.markdown(log["content"])

# ---------------------------------------------------------------------------
# Step 10 — Export
# ---------------------------------------------------------------------------

with st.container(border=True):
    col1, col2 = st.columns([8, 2])
    col1.subheader("⑩ Export")
    col2.caption("")

    graphml_files = []
    if os.path.isdir(ctx.output_dir):
        graphml_files = glob.glob(os.path.join(ctx.output_dir, "*.graphml"))

    if graphml_files:
        st.write("**Existing exports:**")
        for f in graphml_files:
            fname = os.path.basename(f)
            file_size = os.path.getsize(f)
            col_name, col_dl = st.columns([6, 2])
            col_name.text(f"{fname} ({file_size:,} bytes)")
            with open(f, "rb") as fh:
                col_dl.download_button(
                    label="Download",
                    data=fh,
                    file_name=fname,
                    mime="application/xml",
                    key=f"dl_{fname}",
                )

    if st.button("▶ Export Graph", key="run_export"):
        if not get_api_key():
            st.error("Set a Gemini API key in the sidebar first.")
        else:
            try:
                with st.spinner("Exporting graph to GraphML..."):
                    dst = make_runner(ctx).run_export()
                st.success(f"Exported to {dst}")
                st.rerun()
            except Exception as e:
                st.error(f"Export failed: {e}")
