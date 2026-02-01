import unittest
from unittest.mock import MagicMock, patch
from services.graph_service import GraphService

class TestSchemaExtraction(unittest.TestCase):
    def setUp(self):
        self.mock_driver = MagicMock()
        self.service = GraphService()
        self.service.driver = self.mock_driver
    
    def test_get_schema_visualization_fallback(self):
        # Mocking generic response
        mock_result = [{"source": "Person", "target": "Organization", "type": "WORKS_FOR"}]
        
        # We need to simulate the send_query method or connection
        with patch.object(self.service, 'send_query', return_value=mock_result) as mock_send:
            with patch.object(self.service, 'connect', return_value=True):
                schema = self.service.get_schema_visualization()
                self.assertEqual(schema, mock_result)
                # Should have tried apoc.meta.schema first, then data if failed?
                # In our code, we try schema, if it returns "value", we use it.
                # If send_query returns list of dicts.
    
    def test_validate_cypher_valid(self):
        with patch.object(self.service, 'connect', return_value=True):
            session_mock = MagicMock()
            self.mock_driver.session.return_value.__enter__.return_value = session_mock
            
            valid, error = self.service.validate_cypher("MATCH (n) RETURN n")
            self.assertTrue(valid)
            self.assertIsNone(error)
            session_mock.run.assert_called_with("EXPLAIN MATCH (n) RETURN n")

    def test_validate_cypher_invalid(self):
        with patch.object(self.service, 'connect', return_value=True):
            session_mock = MagicMock()
            session_mock.run.side_effect = Exception("Syntax Error")
            self.mock_driver.session.return_value.__enter__.return_value = session_mock
            
            valid, error = self.service.validate_cypher("MATCH n RETURN")
            self.assertFalse(valid)
            self.assertEqual(error, "Syntax Error")

if __name__ == '__main__':
    unittest.main()
