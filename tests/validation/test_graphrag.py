
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import os
import tempfile
import shutil
from pathlib import Path

from agents.kg_pipeline_agent import MarkdownDataLoader, RegexTextSplitter, KgPipelineAgent
from services.gemini_graphrag import GeminiLLM, GeminiEmbedder
from neo4j_graphrag.experimental.components.types import TextChunk

class TestGraphRAGComponents(unittest.IsolatedAsyncioTestCase):

    def test_markdown_loader_title(self):
        loader = MarkdownDataLoader()
        text = "# Analysis of Product X\n\nThis is a review."
        title = loader.extract_title(text)
        self.assertEqual(title, "Analysis of Product X")
        
        text_no_title = "Just some text."
        self.assertEqual(loader.extract_title(text_no_title), "Untitled")

    async def test_regex_splitter(self):
        splitter = RegexTextSplitter(pattern="---")
        text = "Chunk 1\n---\nChunk 2\n---\nChunk 3"
        chunks_obj = await splitter.run(text)
        chunks = chunks_obj.chunks
        
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].text, "Chunk 1")
        self.assertEqual(chunks[1].text, "Chunk 2")
        self.assertEqual(chunks[2].text, "Chunk 3")

    def test_gemini_adapter_init(self):
        # Just check it initializes without exploding if key is present
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            llm = GeminiLLM()
            self.assertEqual(llm.model_name, "gemini-3-pro-preview")
            
            embedder = GeminiEmbedder()
            self.assertEqual(embedder.model, "text-embedding-004")

class TestKgPipelineAgent(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, 'user_data'), exist_ok=True)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('agents.kg_pipeline_agent.SimpleKGPipeline')
    @patch('agents.kg_pipeline_agent.graphdb')
    async def test_run_pipeline_flow(self, mock_graphdb, mock_pipeline_cls):
        # Setup
        mock_graphdb.connect.return_value = True
        
        # Create a dummy file
        fpath = os.path.join(self.test_dir, 'user_data', 'test.md')
        with open(fpath, 'w') as f:
            f.write("# Test Doc\n---\nContent")
            
        agent = KgPipelineAgent(api_key="fake", data_dir=self.test_dir)
        
        # Test Run
        await agent.run_pipeline(['test.md'])
        
        # Assert Pipeline was initialized
        mock_pipeline_cls.assert_called_once()
        # Assert Run was called
        mock_pipeline_cls.return_value.run_async.assert_called_once()

if __name__ == '__main__':
    unittest.main()
