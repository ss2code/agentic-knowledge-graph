import unittest
from unittest.mock import patch, MagicMock
import json
import os
import shutil
import tempfile
from agents.extraction_agent import ExtractionSchemaLoop

class TestPhase4Extraction(unittest.TestCase):

    def setUp(self):
        # Create a temp directory for this test run
        self.test_dir = tempfile.mkdtemp()
        
        # 1. Mock Intent
        with open(os.path.join(self.test_dir, 'user_intent.json'), 'w') as f:
            json.dump({
                "intent": "Analyze Reviews", 
                "description": "Find complaints in reviews",
            }, f)

        # 2. Mock Approved Files
        review_path = os.path.join(self.test_dir, 'reviews.txt')
        with open(os.path.join(self.test_dir, 'approved_files.json'), 'w') as f:
            json.dump({"files": [review_path]}, f)

        # 3. Mock Data File
        with open(review_path, 'w') as f:
            f.write("User: Bob\nRating: 1\nText: This product broke immediately.")

        # 4. Mock Construction Plan (Constraint for NER)
        with open(os.path.join(self.test_dir, 'construction_plan.json'), 'w') as f:
            json.dump({
                "nodes": [{"label": "Product", "source_file": "products.csv"}]
            }, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('agents.extraction_agent.NERAgent._generate')
    @patch('agents.extraction_agent.FactExtractionAgent._generate')
    @patch('builtins.input') # Mock User Approval
    def test_extraction_loop_success(self, mock_input, mock_fact_gen, mock_ner_gen):
        """Simulate a successful pass through both gates."""
        
        # Setup Mocks
        mock_input.side_effect = ['A', 'A'] # Approve Entities, Approve Facts
        
        # NER Output
        mock_ner_gen.return_value = (json.dumps({
            "entity_types": ["Product", "Review", "Complaint"],
            "reasoning": "Standard approach."
        }), "mock-ner-model")
        
        # Fact Output
        mock_fact_gen.return_value = (json.dumps({
            "facts": [
                {"subject": "Review", "predicate": "MENTIONS", "object": "Product"},
                {"subject": "Review", "predicate": "HAS_COMPLAINT", "object": "Complaint"}
            ],
            "reasoning": "Linking entities."
        }), "mock-fact-model")
        
        # Run Loop
        loop = ExtractionSchemaLoop(verbose=True, api_key='mock_key', data_dir=self.test_dir)
        result = loop.run()
        
        # Assertions
        self.assertTrue(result)
        out_path = os.path.join(self.test_dir, 'extraction_plan.json')
        self.assertTrue(os.path.exists(out_path))
        
        with open(out_path, 'r') as f:
            plan = json.load(f)
            self.assertEqual(len(plan['entities']), 3)
            self.assertEqual(len(plan['facts']), 2)
            self.assertEqual(plan['model_used'], "mock-fact-model")
            
        print("\n✅ Phase 4 Happy Path Passed")

if __name__ == '__main__':
    unittest.main()
