import unittest
from unittest.mock import patch, MagicMock
from agents.schema_agent import BaseAgent
import time

class TestQuotaHandling(unittest.TestCase):
    
    @patch('agents.schema_agent.time.sleep')
    @patch('agents.schema_agent.genai.Client')
    def test_smart_backoff(self, mock_client_cls, mock_sleep):
        """Verify that we parse the retry time and sleep correctly."""
        
        # Setup
        agent = BaseAgent(api_key="mock")
        mock_instance = mock_client_cls.return_value
        
        # Simulate Error with explicit time
        error_msg = "429 RESOURCE_EXHAUSTED ... Please retry in 5.5s."
        
        # Side effect: Fail twice with 429, then succeed
        mock_instance.models.generate_content.side_effect = [
            Exception(error_msg),
            Exception(error_msg),
            MagicMock(text="Success")
        ]
        
        # Run
        result = agent._generate("prompt")
        
        # Verify
        self.assertEqual(result, "Success")
        self.assertEqual(mock_sleep.call_count, 2)
        
        # Verify sleep duration (5.5 + 1 = 6.5s)
        # Note: Depending on float precision, we check approximate
        args, _ = mock_sleep.call_args
        self.assertAlmostEqual(args[0], 6.5, delta=0.1)
        print("✅ Test Passed: Parsed '5.5s' and slept for ~6.5s.")

if __name__ == '__main__':
    unittest.main()
