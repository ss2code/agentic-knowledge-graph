import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from core.context import Context
from utils.pipeline_runner import PipelineRunner

class TestPipelineRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "user_data"), exist_ok=True)
        os.makedirs(os.path.join(self.tmp, "debug"), exist_ok=True)
        os.makedirs(os.path.join(self.tmp, "output"), exist_ok=True)
        self.ctx = Context.from_path(self.tmp)
        self.runner = PipelineRunner(self.ctx, api_key="test-key")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    @patch("agents.intent_agent.IntentAgent")
    def test_run_intent_calls_refine_and_marks_state(self, MockIntentAgent):
        mock_agent = MagicMock()
        mock_agent.refine_intent_from_text.return_value = {"intent": "Test KG"}
        MockIntentAgent.return_value = mock_agent

        result = self.runner.run_intent("Build a test KG")

        mock_agent.refine_intent_from_text.assert_called_once_with("Build a test KG")
        self.assertEqual(result["intent"], "Test KG")

    def test_approve_files_scans_and_saves(self):
        # Create a fake file in user_data
        test_file = os.path.join(self.ctx.data_dir, "test.csv")
        with open(test_file, "w") as f:
            f.write("col1,col2\n1,2\n")

        approved = self.runner.approve_files()

        self.assertIn(test_file, approved)
        # Check approved_files.json was written
        approved_path = os.path.join(self.tmp, "approved_files.json")
        self.assertTrue(os.path.exists(approved_path))
        with open(approved_path) as f:
            data = json.load(f)
        self.assertIn(test_file, data["files"])

    def test_approve_files_accepts_selected_paths_kwarg(self):
        """Regression: approve_files() must accept selected_paths as a keyword argument.
        This was broken when the UI called approve_files(selected_paths=[...]) against
        a version of PipelineRunner that only accepted positional scan-all behavior."""
        explicit_paths = ["/some/dir/products.csv", "/some/dir/reviews.txt"]
        approved = self.runner.approve_files(selected_paths=explicit_paths)

        self.assertEqual(approved, explicit_paths)
        approved_path = os.path.join(self.tmp, "approved_files.json")
        with open(approved_path) as f:
            data = json.load(f)
        self.assertEqual(data["files"], explicit_paths)

    def test_approve_files_selected_paths_overrides_scan(self):
        """When selected_paths is given, it is used directly (no dir scan)."""
        # Put a file in user_data that should NOT appear in results
        decoy = os.path.join(self.ctx.data_dir, "decoy.csv")
        with open(decoy, "w") as f:
            f.write("x\n")

        explicit = ["/explicit/path/chosen.csv"]
        approved = self.runner.approve_files(selected_paths=explicit)

        self.assertNotIn(decoy, approved)
        self.assertEqual(approved, explicit)

    @patch("agents.schema_agent.SchemaRefinementLoop")
    def test_run_schema_negotiation_calls_loop(self, MockLoop):
        mock_loop = MagicMock()
        mock_loop.run.return_value = True
        MockLoop.return_value = mock_loop

        # Create a fake construction_plan.json
        plan = {"rule_1": {"construction_type": "node", "label": "TestNode"}}
        with open(os.path.join(self.tmp, "construction_plan.json"), "w") as f:
            json.dump(plan, f)

        result = self.runner.run_schema_negotiation()

        mock_loop.run.assert_called_once()
        self.assertIn("rule_1", result)

    @patch("agents.extraction_agent.ExtractionSchemaLoop")
    def test_propose_entities_returns_dict_without_saving(self, MockLoop):
        mock_loop = MagicMock()
        mock_loop.propose_entities_step.return_value = {
            "entity_types": ["Restaurant", "Menu"], "reasoning": "test"
        }
        MockLoop.return_value = mock_loop

        result = self.runner.propose_entities()

        mock_loop.propose_entities_step.assert_called_once()
        self.assertIn("entity_types", result)
        # No extraction_plan.json should be written
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "extraction_plan.json")))

    @patch("agents.extraction_agent.ExtractionSchemaLoop")
    def test_propose_facts_returns_dict_without_saving(self, MockLoop):
        mock_loop = MagicMock()
        mock_loop.propose_facts_step.return_value = {
            "facts": [{"subject": "A", "predicate": "HAS", "object": "B"}],
            "reasoning": "test",
            "model_used": "gemini-2.0-flash"
        }
        MockLoop.return_value = mock_loop

        result = self.runner.propose_facts(["Restaurant", "Menu"])

        mock_loop.propose_facts_step.assert_called_once_with(["Restaurant", "Menu"])
        self.assertIn("facts", result)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "extraction_plan.json")))

    @patch("agents.extraction_agent.ExtractionSchemaLoop")
    def test_save_extraction_plan_writes_json(self, MockLoop):
        mock_loop = MagicMock()
        MockLoop.return_value = mock_loop

        self.runner.save_extraction_plan(
            entities=["Restaurant"],
            facts=[{"subject": "Restaurant", "predicate": "HAS", "object": "Menu"}],
            model="gemini-2.0-flash"
        )

        mock_loop.save_plan.assert_called_once_with(
            ["Restaurant"],
            [{"subject": "Restaurant", "predicate": "HAS", "object": "Menu"}],
            "gemini-2.0-flash"
        )
