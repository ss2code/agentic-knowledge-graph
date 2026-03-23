import unittest
from unittest.mock import patch, MagicMock
import os

from agents.intent_agent import IntentAgent
from agents.schema_agent import BaseAgent


class TestSimulationMode(unittest.TestCase):
    """Agents run in simulation mode when PROJECT_ANTHROPIC_API_KEY is not set."""

    @patch.dict(os.environ, {}, clear=True)
    def test_base_agent_simulation_mode_no_key(self):
        """BaseAgent.provider is None when PROJECT_ANTHROPIC_API_KEY is absent."""
        # Ensure key is not set
        os.environ.pop("PROJECT_ANTHROPIC_API_KEY", None)
        agent = BaseAgent()
        self.assertIsNone(agent.provider)

    @patch.dict(os.environ, {}, clear=True)
    def test_base_agent_generate_simulation_returns_json(self):
        """_generate() returns a JSON string and 'simulation-model' in simulation mode."""
        os.environ.pop("PROJECT_ANTHROPIC_API_KEY", None)
        agent = BaseAgent()
        text, model = agent._generate("some prompt")
        self.assertEqual(model, "simulation-model")
        self.assertIn("SIMULATION MODE", text)

    @patch.dict(os.environ, {}, clear=True)
    def test_intent_agent_simulation_mode(self):
        """IntentAgent enters simulation mode when no key is set."""
        os.environ.pop("PROJECT_ANTHROPIC_API_KEY", None)
        agent = IntentAgent()
        self.assertIsNone(agent.provider)

    @patch.dict(os.environ, {}, clear=True)
    def test_intent_agent_refine_intent_simulation_trace(self):
        """IntentAgent.refine_intent 'Trace X to Y' heuristic works in simulation."""
        os.environ.pop("PROJECT_ANTHROPIC_API_KEY", None)
        agent = IntentAgent()
        is_valid, response_json = agent.refine_intent("Trace Complaints to Ingredients")
        self.assertTrue(is_valid)
        self.assertIn("Trace Complaints to Ingredients", response_json)

    @patch.dict(os.environ, {}, clear=True)
    def test_intent_agent_refine_intent_simulation_analyze(self):
        """IntentAgent.refine_intent 'Analyze X' heuristic works in simulation."""
        os.environ.pop("PROJECT_ANTHROPIC_API_KEY", None)
        agent = IntentAgent()
        is_valid, response_json = agent.refine_intent("Analyze Revenue")
        self.assertTrue(is_valid)
        self.assertIn("Analyze Revenue", response_json)

    @patch.dict(os.environ, {}, clear=True)
    def test_intent_agent_refine_intent_simulation_vague(self):
        """Vague intent returns False in simulation."""
        os.environ.pop("PROJECT_ANTHROPIC_API_KEY", None)
        agent = IntentAgent()
        is_valid, _ = agent.refine_intent("Just do something")
        self.assertFalse(is_valid)


class TestAnthropicProviderWithMock(unittest.TestCase):
    """BaseAgent._generate() calls AnthropicProvider when key is set."""

    @patch("anthropic.Anthropic")
    @patch.dict(os.environ, {"PROJECT_ANTHROPIC_API_KEY": "test-key"})
    def test_base_agent_generate_calls_provider(self, MockAnthropic):
        """_generate() returns provider output when PROJECT_ANTHROPIC_API_KEY is set."""
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"nodes": [], "relationships": []}')]
        mock_client.messages.create.return_value = mock_response

        agent = BaseAgent(model_name="claude-haiku-4-5-20251001")
        text, model = agent._generate("some prompt", function_name="test_fn")

        self.assertEqual(model, "claude-haiku-4-5-20251001")
        self.assertIn("nodes", text)
        mock_client.messages.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
