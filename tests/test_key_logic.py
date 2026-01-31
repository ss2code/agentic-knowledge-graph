import unittest
from unittest.mock import patch, MagicMock, ANY
from agents.intent_agent import IntentAgent
import os

class TestIntentAgentLogic(unittest.TestCase):
    
    @patch('agents.intent_agent.input')
    @patch('os.getenv')
    def test_init_simulation_mode(self, mock_getenv, mock_input):
        """Test fallback to simulation when no key is provided."""
        mock_getenv.return_value = None
        mock_input.return_value = "" # User skips entry
        
        agent = IntentAgent()
        
        self.assertIsNone(agent.client)
        print("✅ Test 1 Passed: Correctly entered Simulation Mode (No Client).")

    @patch('agents.intent_agent.genai.Client')
    @patch('agents.intent_agent.input')
    @patch('os.getenv')
    def test_init_with_valid_key_input(self, mock_getenv, mock_input, mock_client_cls):
        """Test initializing with a key provided via input."""
        mock_getenv.return_value = None
        mock_input.return_value = "secret_key"
        
        # Mock client behavior for validation check
        mock_client_instance = mock_client_cls.return_value
        mock_client_instance.models.generate_content.return_value = MagicMock(text="OK")
        
        agent = IntentAgent()
        
        self.assertIsNotNone(agent.client)
        # Verify it tried to validate with the temp client
        mock_client_cls.assert_called_with(api_key="secret_key")
        print("✅ Test 2 Passed: API Key from input was validated and accepted.")

    @patch('agents.intent_agent.genai.Client')
    @patch('os.getenv')
    def test_refine_intent_api_success(self, mock_getenv, mock_client_cls):
        """Test intent refinement using the API (happy path)."""
        mock_getenv.return_value = "env_key"
        
        mock_client_instance = mock_client_cls.return_value
        # Mock the response for refine_intent -> _generate_with_fallback
        mock_response = MagicMock()
        mock_response.text = '{"intent": "Test", "description": "Desc", "primary_entities": [], "reasoning": "R"}'
        mock_client_instance.models.generate_content.return_value = mock_response
        
        agent = IntentAgent()
        
        is_valid, response_text = agent.refine_intent("Trace A to B")
        
        self.assertTrue(is_valid)
        self.assertIn("Test", response_text)
        print("✅ Test 3 Passed: refine_intent executed successfully with API.")

    @patch('agents.intent_agent.input')
    @patch('os.getenv')
    def test_refine_intent_simulation_mode(self, mock_getenv, mock_input):
        """Test the regex logic in simulation mode."""
        mock_getenv.return_value = None
        mock_input.return_value = "" # Skip key -> Simulation
        
        agent = IntentAgent()
        
        # Test "Trace X to Y" heuristic
        is_valid, response_json = agent.refine_intent("Trace Complaints to Ingredients")
        self.assertTrue(is_valid)
        self.assertIn("Trace Complaints to Ingredients", response_json)
        
        # Test "Analyze X" heuristic
        is_valid, response_json = agent.refine_intent("Analyze Revenue")
        self.assertTrue(is_valid)
        self.assertIn("Analyze Revenue", response_json)
        
        # Test Vague
        is_valid, response_msg = agent.refine_intent("Just do something")
        self.assertFalse(is_valid)
        
        print("✅ Test 4 Passed: Simulation heuristics are working.")

    @patch('agents.intent_agent.input')
    @patch('agents.intent_agent.genai.Client')
    @patch('os.getenv')
    def test_fallback_retry_logic(self, mock_getenv, mock_client_cls, mock_input):
        """Test that _generate_with_fallback retries on failure."""
        mock_getenv.return_value = "env_key"
        # Since env key is "env_key", _get_valid_api_key will try to validate it.
        # It will create a temporary client, which comes from mock_client_cls.
        # We need to ensure that validation passes or we skip input.
        # Let's just mock input to return nothing so we don't hang if validation fails.
        mock_input.return_value = ""
        mock_client_instance = mock_client_cls.return_value
        
        # Setup side_effect to simulate failures then success
        # 1. 429 Error (Rate Limit)
        # 2. 404 Error (Not Found)
        # 3. Success
        error_429 = Exception("429 RESOURCE_EXHAUSTED")
        error_404 = Exception("404 Not Found")
        success_response = MagicMock(text="Success")
        
        mock_client_instance.models.generate_content.side_effect = [error_429, error_404, success_response]
        
        # Verify validation call was skipped or mocked
        # IMPORTANT: We need agent.client to be set for _generate_with_fallback to work.
        # Since _validate_key might fail in test env, we force it.
        agent = IntentAgent()
        agent.client = mock_client_instance
        
        # We need to mock time.sleep to avoid waiting during tests
        with patch('agents.intent_agent.time.sleep') as mock_sleep:
            response = agent._generate_with_fallback("Prompt")
        
        self.assertEqual(response.text, "Success")
        # Verify it retried: 1st call (429), 2nd call (404), 3rd call (Success)
        self.assertEqual(mock_client_instance.models.generate_content.call_count, 3)
        print("✅ Test 5 Passed: Retry/Fallback logic handled errors correctly.")

if __name__ == '__main__':
    unittest.main()
