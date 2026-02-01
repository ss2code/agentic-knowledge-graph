import unittest
from unittest.mock import patch, MagicMock
import json
import os
import shutil
import tempfile
from agents.schema_agent import SchemaRefinementLoop

class TestPhase3Schema(unittest.TestCase):

    def setUp(self):
        # Create a temp directory for this test run
        self.test_dir = tempfile.mkdtemp()
        
        # Mock Intent
        with open(os.path.join(self.test_dir, 'user_intent.json'), 'w') as f:
            json.dump({
                "intent": "Test Trace", 
                "description": "Tracing A to B",
                "primary_entities": ["A", "B"]
            }, f)

        # Mock Approved Files
        # Note: The 'files' list must point to real files. We'll put them in the temp dir too.
        csv_path = os.path.join(self.test_dir, 'test_file.csv')
        with open(os.path.join(self.test_dir, 'approved_files.json'), 'w') as f:
            json.dump({"files": [csv_path]}, f)

        # Mock Data File
        with open(csv_path, 'w') as f:
            f.write("id,source,target\n1,X,Y")
            
        # Ensure debug dir exists
        os.makedirs(os.path.join(self.test_dir, 'debug'), exist_ok=True)

    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir)

    @patch('agents.schema_agent.SchemaProposalAgent._generate')
    @patch('agents.schema_agent.SchemaCriticAgent._generate')
    def test_successful_negotation(self, mock_critic, mock_proposer):
        """Simulates a 1-shot success."""
        
        # 1. Proposer Output (Mocked)
        mock_proposer.return_value = (json.dumps({
            "NodeA": {
                "construction_type": "node",
                "label": "NodeA",
                "unique_column_name": "id",
                "source_file": "test_file.csv"
            }
        }), "mock-model-proposer")
        
        # 2. Critic Output (Mocked) - Valid
        mock_critic.return_value = (json.dumps({
            "status": "VALID",
            "feedback": "LGTM"
        }), "mock-model-critic")
        
        # INJECT THE TEMP DIR
        loop = SchemaRefinementLoop(verbose=True, api_key='mock_key', data_dir=self.test_dir)
        result = loop.run()
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'construction_plan.json')))
        
        
        # Log verification removed as _generate is mocked and thus logs are not written.

        
        # Verify that file context was passed to the Critic's prompt
        # contents arg of _generate(self, contents=...)
        critic_call_args = mock_critic.call_args
        # Depending on how it's called (args vs kwargs), we check the string
        critic_prompt = critic_call_args[1].get('contents', critic_call_args[0][0] if critic_call_args[0] else "")
        self.assertIn("test_file.csv", critic_prompt, "Critic prompt missing filename")
        self.assertIn("id,source,target", critic_prompt, "Critic prompt missing file header/content")
        
        print("\n✅ Test 1 (Happy Path) Passed")

    @patch('agents.schema_agent.SchemaProposalAgent._generate')
    @patch('agents.schema_agent.SchemaCriticAgent._generate')
    def test_retry_logic(self, mock_critic, mock_proposer):
        """Simulates a retry iteration."""
        
        # Proposer: Invalid First, Valid Second
        bad_json = '{"nodes": ... INVALID ...'
        good_json = json.dumps({
            "NodeB": {
                "construction_type": "node", 
                "label": "NodeB",
                "unique_column_name": "id",
                "source_file": "test_file.csv"
            }
        })
        
        mock_proposer.side_effect = [(bad_json, "mock-model"), (good_json, "mock-model")]
        mock_critic.return_value = (json.dumps({"status": "VALID", "feedback": "Nice"}), "mock-model-critic")
        
        # INJECT THE TEMP DIR
        loop = SchemaRefinementLoop(verbose=True, api_key='mock_key', data_dir=self.test_dir)
        result = loop.run()
        
        self.assertTrue(result)
        print("\n✅ Test 2 (Retry Logic) Passed")

if __name__ == '__main__':
    unittest.main()
