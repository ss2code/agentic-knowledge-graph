"""
PipelineRunner: thin wrapper that drives the KG pipeline stages for the Streamlit UI.

All agent imports are deferred (inside methods) to avoid heavy initialization at
import time and keep the web UI responsive.
"""

import asyncio
import json
import os

from core.context import Context
from state_manager import StateManager
from services.llm_provider import AnthropicProvider


class PipelineRunner:
    def __init__(self, context: Context, model_name: str = None):
        """
        Store context and model_name.
        PROJECT_ANTHROPIC_API_KEY is read from the environment by AnthropicProvider — no need to
        pass it through here.
        Creates a StateManager bound to context.base_path.
        Does NOT start Neo4j or Docker containers — call ensure_neo4j() before graph stages.
        """
        self.context = context
        self.model_name = model_name or AnthropicProvider.DEFAULT_MODEL
        self.sm = StateManager(base_path=context.base_path)

    def ensure_neo4j(self) -> bool:
        """Start the per-context Neo4j container if it is not already running (idempotent)."""
        from services.container_service import ContainerService
        svc = ContainerService(self.context)
        if not svc.is_running():
            print("Neo4j is not running for this context. Starting...")
            return svc.start_container()
        return True

    # ------------------------------------------------------------------
    # Stage 1 – Intent
    # ------------------------------------------------------------------

    def run_intent(self, goal: str) -> dict:
        from agents.intent_agent import IntentAgent

        agent = IntentAgent(data_dir=self.context.base_path, model_name=self.model_name)
        result = agent.refine_intent_from_text(goal)
        self.sm.mark_intent_updated()
        return result

    # ------------------------------------------------------------------
    # Stage 2 – File approval
    # ------------------------------------------------------------------

    def approve_files(self, selected_paths: list | None = None) -> list:
        """
        Persist approved_files.json and mark files as approved.

        If selected_paths is given, use it directly (absolute paths).
        Otherwise fall back to scanning context.data_dir for non-hidden files.
        Returns the list of approved absolute paths.
        """
        if selected_paths is not None:
            approved_paths = selected_paths
        else:
            data_dir = self.context.data_dir
            if os.path.isdir(data_dir):
                files = [f for f in os.listdir(data_dir) if not f.startswith('.')]
            else:
                files = []
            approved_paths = [os.path.join(data_dir, f) for f in files]

        approved_data = {"files": approved_paths}

        save_path = os.path.join(self.context.base_path, 'approved_files.json')
        with open(save_path, 'w') as fh:
            json.dump(approved_data, fh, indent=2)

        self.sm.mark_files_approved()
        return approved_paths

    # ------------------------------------------------------------------
    # Stage 3 – Schema negotiation
    # ------------------------------------------------------------------

    def run_schema_negotiation(self) -> dict:
        from agents.schema_agent import SchemaRefinementLoop

        loop = SchemaRefinementLoop(
            data_dir=self.context.base_path,
            model_name=self.model_name,
        )
        success = loop.run()
        if success:
            self.sm.mark_schema_valid()

        plan_path = os.path.join(self.context.base_path, 'construction_plan.json')
        if os.path.exists(plan_path):
            with open(plan_path, 'r') as fh:
                return json.load(fh)
        return {}

    # ------------------------------------------------------------------
    # Stage 4 – Extraction design (stepped)
    # ------------------------------------------------------------------

    def propose_entities(self) -> dict:
        from agents.extraction_agent import ExtractionSchemaLoop

        loop = ExtractionSchemaLoop(
            data_dir=self.context.base_path,
            model_name=self.model_name,
        )
        return loop.propose_entities_step()

    def propose_facts(self, entities: list) -> dict:
        from agents.extraction_agent import ExtractionSchemaLoop

        loop = ExtractionSchemaLoop(
            data_dir=self.context.base_path,
            model_name=self.model_name,
        )
        return loop.propose_facts_step(entities)

    def save_extraction_plan(self, entities: list, facts: list, model: str = None) -> None:
        from agents.extraction_agent import ExtractionSchemaLoop

        loop = ExtractionSchemaLoop(
            data_dir=self.context.base_path,
            model_name=model or self.model_name,
        )
        loop.sm = self.sm
        loop.save_plan(entities, facts, model or self.model_name)

    # ------------------------------------------------------------------
    # Stage 5 – Graph build
    # ------------------------------------------------------------------

    def run_graph_build(self, strategy: str = 'H', progress_callback=None) -> bool:
        self.ensure_neo4j()
        from agents.graph_builder import GraphBuilderAgent

        agent = GraphBuilderAgent(
            model_name=self.model_name,
            context=self.context,
            progress_callback=progress_callback,
        )
        success = agent.build_graph(global_strategy=strategy)
        if success:
            self.sm.mark_graph_built()
        return bool(success)

    # ------------------------------------------------------------------
    # Stage 5 (alt) – KG pipeline (unstructured text)
    # ------------------------------------------------------------------

    def run_kg_pipeline(self, files: list) -> bool:
        self.ensure_neo4j()
        import concurrent.futures
        from agents.kg_pipeline_agent import KgPipelineAgent

        agent = KgPipelineAgent(
            data_dir=self.context.base_path,
            model_name=self.model_name,
        )
        # Run in a worker thread so asyncio.run() creates a fresh event loop,
        # avoiding RuntimeError when called from within Streamlit's running loop.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, agent.run_pipeline(files))
            future.result()  # re-raises any exception from the pipeline
        agent.resolve_entities()
        self.sm.mark_graphrag_complete()
        return True

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def run_visualization(self) -> str:
        from agents.visualizer_agent import VisualizerAgent

        viz = VisualizerAgent(context=self.context)
        viz.run()
        html_path = os.path.join(self.context.output_dir, 'schema_viz.html')
        if not os.path.exists(html_path):
            raise RuntimeError(f"Visualization failed: {html_path} was not created")
        return html_path

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def run_export(self) -> str:
        from services.graph_service import graphdb

        filename = f"{self.context.name}_dump.graphml"
        if not graphdb.export_graph(filename):
            raise RuntimeError(f"export_graph() failed for {filename}")
        src = os.path.join(self.context.data_dir, filename)
        dst = os.path.join(self.context.output_dir, filename)
        if os.path.exists(src):
            os.replace(src, dst)
        return dst

    # ------------------------------------------------------------------
    # Text-to-Cypher query
    # ------------------------------------------------------------------

    def run_text_to_cypher(self, query: str) -> tuple:
        from agents.text_to_cypher_agent import TextToCypherAgent

        agent = TextToCypherAgent(
            debug_dir=self.context.debug_dir,
            model_name=self.model_name,
        )
        cypher = agent.generate_query_with_retry(query)
        results = agent.execute_query(cypher)
        return (cypher, results)
