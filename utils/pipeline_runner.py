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


class PipelineRunner:
    def __init__(self, context: Context, api_key: str):
        """
        Store context and api_key.
        Sets GEMINI_API_KEY in the environment if api_key is truthy.
        Creates a StateManager bound to context.base_path.
        Does NOT start Neo4j or Docker containers.
        """
        self.context = context
        self.api_key = api_key
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
        self.sm = StateManager(base_path=context.base_path)

    # ------------------------------------------------------------------
    # Stage 1 – Intent
    # ------------------------------------------------------------------

    def run_intent(self, goal: str) -> dict:
        """
        Drive the IntentAgent with a plain-text goal string.
        Marks intent as updated on success.
        Returns the intent dict.
        """
        from agents.intent_agent import IntentAgent

        agent = IntentAgent(data_dir=self.context.base_path)
        result = agent.refine_intent_from_text(goal)
        self.sm.mark_intent_updated()
        return result

    # ------------------------------------------------------------------
    # Stage 2 – File approval
    # ------------------------------------------------------------------

    def approve_files(self) -> list:
        """
        Scan context.data_dir for non-hidden files, persist approved_files.json,
        mark files as approved, and return the list of approved absolute paths.
        """
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
        """
        Run the SchemaRefinementLoop.
        Marks schema as valid if the loop reports success.
        Returns the construction_plan.json dict, or {} if the file is missing.
        """
        from agents.schema_agent import SchemaRefinementLoop

        loop = SchemaRefinementLoop(
            api_key=self.api_key,
            data_dir=self.context.base_path,
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
        """
        Ask the ExtractionSchemaLoop to propose entity types.
        Returns the proposal dict.
        """
        from agents.extraction_agent import ExtractionSchemaLoop

        loop = ExtractionSchemaLoop(
            api_key=self.api_key,
            data_dir=self.context.base_path,
        )
        return loop.propose_entities_step()

    def propose_facts(self, entities: list) -> dict:
        """
        Ask the ExtractionSchemaLoop to propose facts for the given entity list.
        Returns the proposal dict.
        """
        from agents.extraction_agent import ExtractionSchemaLoop

        loop = ExtractionSchemaLoop(
            api_key=self.api_key,
            data_dir=self.context.base_path,
        )
        return loop.propose_facts_step(entities)

    def save_extraction_plan(self, entities: list, facts: list, model: str) -> None:
        """
        Persist the extraction plan via ExtractionSchemaLoop.save_plan().
        Injects self.sm so that save_plan can call mark_extraction_designed().
        """
        from agents.extraction_agent import ExtractionSchemaLoop

        loop = ExtractionSchemaLoop(
            api_key=self.api_key,
            data_dir=self.context.base_path,
        )
        loop.sm = self.sm
        loop.save_plan(entities, facts, model)

    # ------------------------------------------------------------------
    # Stage 5 – Graph build
    # ------------------------------------------------------------------

    def run_graph_build(self) -> bool:
        """
        Drive the GraphBuilderAgent to populate Neo4j.
        Marks graph as built on success.
        Returns True/False.
        """
        from agents.graph_builder import GraphBuilderAgent

        agent = GraphBuilderAgent(
            api_key=self.api_key,
            context=self.context,
        )
        success = agent.build_graph()
        if success:
            self.sm.mark_graph_built()
        return bool(success)

    # ------------------------------------------------------------------
    # Stage 5 (alt) – KG pipeline (unstructured text)
    # ------------------------------------------------------------------

    def run_kg_pipeline(self, files: list) -> bool:
        """
        Run KgPipelineAgent for unstructured text files.
        Returns True on success, False if an exception is raised.
        """
        from agents.kg_pipeline_agent import KgPipelineAgent

        try:
            agent = KgPipelineAgent(
                api_key=self.api_key,
                data_dir=self.context.base_path,
            )
            asyncio.run(agent.run_pipeline(files))
            agent.resolve_entities()
            self.sm.mark_graphrag_complete()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def run_visualization(self) -> str:
        """
        Run the VisualizerAgent to regenerate the schema HTML.
        Returns path to schema_viz.html.
        Raises RuntimeError if the file was not created.
        """
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
        """
        Export the graph to a GraphML file inside context.output_dir.
        Mirrors the Orchestrator.run_export() logic.
        Returns the destination path string.
        """
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
        """
        Translate a natural-language query to Cypher and execute it.
        Returns (cypher_string, result_rows).
        """
        from agents.text_to_cypher_agent import TextToCypherAgent

        agent = TextToCypherAgent(
            api_key=self.api_key,
            debug_dir=self.context.debug_dir,
        )
        cypher = agent.generate_query_with_retry(query)
        results = agent.execute_query(cypher)
        return (cypher, results)
