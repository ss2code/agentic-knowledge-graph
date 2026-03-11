"""
Regression tests for BaseAgent logging behaviour.

Key regression: simulation mode (no API key / no client) must still write
a log entry so that the Streamlit debug expander shows content after a run.
Before the fix, _generate() returned early without calling log_llm_interaction,
causing the debug expander to show "0 interactions" after every step 4 run and
the previous log (from before agent init) to be rotated away with nothing replacing it.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from agents.schema_agent import BaseAgent


class TestBaseAgentSimulationLogging(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def _make_agent(self, module_name="TestAgent"):
        """Create a BaseAgent in simulation mode (no client) with a real debug dir."""
        with patch("core.logging_utils.get_log_file_path",
                   return_value=os.path.join(self.tmp, f"debug_llm_{module_name}_20260101_000000.md")):
            agent = BaseAgent(api_key=None, debug_dir=self.tmp, module_name=module_name)
        agent.client = None  # force simulation mode
        return agent

    def test_simulation_mode_writes_log_file(self):
        """_generate() in simulation mode must create the log file."""
        agent = self._make_agent()
        agent._generate("test prompt", function_name="test_func")
        self.assertTrue(os.path.exists(agent.log_file),
                        "Log file must be created even in simulation mode")

    def test_simulation_mode_log_contains_prompt(self):
        """Simulation log must record the prompt so the expander is useful."""
        agent = self._make_agent()
        agent._generate("my test prompt", function_name="test_func")
        with open(agent.log_file) as f:
            content = f.read()
        self.assertIn("my test prompt", content)

    def test_simulation_mode_log_contains_simulation_marker(self):
        """Simulation log must indicate it was a simulated response."""
        agent = self._make_agent()
        agent._generate("any prompt", function_name="test_func")
        with open(agent.log_file) as f:
            content = f.read()
        self.assertIn("SIMULATION MODE", content)

    def test_simulation_mode_returns_correct_tuple(self):
        """_generate() simulation path must still return (json_str, model_name)."""
        agent = self._make_agent()
        result, model = agent._generate("prompt", function_name="f")
        self.assertIsInstance(result, str)
        self.assertEqual(model, "simulation-model")

    def test_no_log_written_when_log_file_is_none(self):
        """If log_file is None, simulation mode must not crash."""
        agent = BaseAgent(api_key=None, debug_dir=None, module_name="NoLog")
        agent.client = None
        agent.log_file = None
        # Should not raise
        result, model = agent._generate("prompt")
        self.assertEqual(model, "simulation-model")
