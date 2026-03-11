import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, PropertyMock
from core.context import Context
from agents.graph_builder import GraphBuilderAgent

class TestGraphBuilderAgent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "debug"), exist_ok=True)
        os.makedirs(os.path.join(self.tmp, "user_data"), exist_ok=True)
        self.ctx = Context.from_path(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def _make_builder(self, api_key=None):
        """Create a GraphBuilderAgent with a mock log path to avoid writing."""
        with patch("agents.graph_builder.graphdb"), \
             patch("core.logging_utils.get_log_file_path", return_value=os.path.join(self.tmp, "debug", "test_log.md")):
            builder = GraphBuilderAgent(api_key=api_key, context=self.ctx)
        builder.log_path = os.path.join(self.tmp, "debug", "test_log.md")
        return builder

    def test_load_construction_plan_raises_on_missing_file(self):
        builder = self._make_builder()
        with self.assertRaises(Exception):
            builder.load_construction_plan()

    def test_load_construction_plan_returns_dict(self):
        plan = {"rule_1": {"construction_type": "node", "label": "TestNode"}}
        plan_path = os.path.join(self.tmp, "construction_plan.json")
        with open(plan_path, "w") as f:
            json.dump(plan, f)

        builder = self._make_builder()
        result = builder.load_construction_plan()
        self.assertEqual(result["rule_1"]["label"], "TestNode")

    @patch("agents.graph_builder.graphdb")
    def test_create_constraints_calls_send_query(self, mock_graphdb):
        mock_graphdb.send_query.return_value = []
        builder = self._make_builder()

        nodes = [{"label": "TestNode", "unique_column_name": "id"}]
        builder.create_constraints(nodes)

        mock_graphdb.send_query.assert_called_once()
        cypher = mock_graphdb.send_query.call_args[0][0]
        self.assertIn("TestNode", cypher)
        self.assertIn("CREATE CONSTRAINT", cypher)

    @patch("agents.graph_builder.graphdb")
    def test_build_graph_returns_false_on_db_connection_failure(self, mock_graphdb):
        mock_graphdb.connect.return_value = False
        builder = self._make_builder()

        result = builder.build_graph()

        self.assertFalse(result)
        mock_graphdb.connect.assert_called_once()
