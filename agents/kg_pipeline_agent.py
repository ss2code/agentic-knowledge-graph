
import os
import json
import re
import asyncio
import random
import traceback
from pathlib import Path
from typing import List, Dict, Any

from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.components.pdf_loader import DataLoader
from neo4j_graphrag.experimental.components.types import PdfDocument, DocumentInfo, TextChunk, TextChunks
from neo4j_graphrag.experimental.components.text_splitters.base import TextSplitter

from services.graph_service import graphdb, CYAN, GREEN, YELLOW, RED, RESET
from services.anthropic_graphrag import AnthropicLLM, SentenceTransformerEmbedder
from agents.schema_agent import BaseAgent


# --- Pipeline Components ---

class RegexTextSplitter(TextSplitter):
    """Split text using regex matched delimiters."""
    def __init__(self, pattern: str = "---"):
        self.pattern = pattern

    async def run(self, text: str) -> TextChunks:
        texts = re.split(self.pattern, text)
        chunks = [TextChunk(text=str(t).strip(), index=i) for (i, t) in enumerate(texts) if t.strip()]
        print(f"{CYAN}  [splitter] Split into {len(chunks)} chunk(s) "
              f"(sizes: {[len(c.text) for c in chunks]}){RESET}")
        return TextChunks(chunks=chunks)

class MarkdownDataLoader(DataLoader):
    def extract_title(self, markdown_text):
        pattern = r'^# (.+)$'
        match = re.search(pattern, markdown_text, re.MULTILINE)
        return match.group(1) if match else "Untitled"

    async def run(self, filepath: Path, metadata = {}) -> PdfDocument:
        with open(filepath, "r") as f:
            markdown_text = f.read()
        doc_headline = self.extract_title(markdown_text)
        markdown_info = DocumentInfo(
            path=str(filepath),
            metadata={
                "title": doc_headline,
            }
        )
        print(f"{CYAN}  [loader] Loaded {len(markdown_text)} chars, title='{doc_headline}'{RESET}")
        return PdfDocument(text=markdown_text, document_info=markdown_info)

# --- Agent ---

class KgPipelineAgent(BaseAgent):
    """
    Agent responsible for the Unstructured Data Pipeline (GraphRAG).
    Extracts entities and relationships from text files using LLMs and builds the graph.
    """
    def __init__(self, api_key=None, data_dir='data', model_name=None):
        super().__init__(model_name=model_name)
        self.data_dir = data_dir
        self.debug_dir = os.path.join(data_dir, 'debug')
        self.llm_adapter = AnthropicLLM(
            model_name=model_name,
            debug_dir=self.debug_dir,
            module_name="KgPipelineInfoExtractor",
        )
        self.embedder_adapter = SentenceTransformerEmbedder()
        self.driver = graphdb.driver  # Use existing driver instance

    def _build_prompt_template(self, context_sample: str) -> str:
        """
        Build a prompt template with a {text} placeholder for the pipeline.

        The neo4j_graphrag pipeline calls template.format(text=<chunk>, schema=..., examples=...)
        so the template MUST contain {{text}} for the actual chunk text to be injected.
        Context from a file sample is baked in for domain awareness.
        """
        # Escape any braces in the context sample so str.format() doesn't choke
        safe_context = context_sample.replace("{", "{{").replace("}", "}}")

        return (
            "You are a knowledge graph builder. Extract entities and relationships "
            "from the input text below.\n\n"
            "Use any appropriate Node Labels (e.g. Product, Issue, Feature, Location, "
            "Ingredient, Person, Review, Restaurant, MenuItem).\n"
            "Use any appropriate Relationship Types (e.g. HAS_ISSUE, MENTIONS, PART_OF, "
            "ORDERED, REVIEWED, CONTAINS).\n\n"
            "Here is a sample from the source document for domain context:\n"
            f"{safe_context[:2000]}\n\n"
            "Schema guidance:\n{{schema}}\n\n"
            "Examples:\n{{examples}}\n\n"
            "Now extract entities and relationships from the following text chunk. "
            "Return ONLY valid JSON with 'nodes' (keys: id, label, properties) "
            "and 'relationships' (keys: start_node_id, end_node_id, type, properties). "
            "Do NOT wrap in markdown code fences.\n\n"
            "Input text:\n{{text}}"
        )

    def _get_representative_sample(self, file_path: str, max_lines=50, small_file_limit=10240):
        """
        Reads a file. If small, returns full content.
        If large, returns first 10 lines + random sample of 'max_lines' from the rest.
        """
        try:
            size = os.path.getsize(file_path)
            if size < small_file_limit:
                 with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                     return f.read()[:3000] # Still cap at 3000 chars

            # Large file strategy
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            if len(lines) <= max_lines:
                return "".join(lines)

            # Take first 10 lines (header context)
            sample = lines[:10]
            # Take random sample from the rest
            rest = lines[10:]
            if rest:
                sample.extend(random.sample(rest, min(len(rest), max_lines)))

            return "".join(sample)[:3000] # Cap total length
        except Exception as e:
            print(f"{RED}Error reading sample from {os.path.basename(file_path)}: {e}{RESET}")
            return ""

    async def run_pipeline(self, file_names: List[str]):
        """Runs the SimpleKGPipeline for a list of files."""
        print(f"\n{CYAN}--- 🚀 Starting GraphRAG Pipeline ---{RESET}")

        if not graphdb.connect():
             print(f"{RED}Neo4j not connected.{RESET}")
             return

        # Notify about logging
        if os.path.exists(self.debug_dir):
            print(f"{CYAN}📝 Logging GraphRAG to: {os.path.join(self.debug_dir, 'debug_llm_KgPipelineInfoExtractor.md')}{RESET}")

        import_dir = os.path.join(self.data_dir, 'user_data')

        # Validation Logic:
        if not os.path.exists(os.path.join(import_dir, file_names[0])):
            # Maybe data_dir IS user_data?
            if os.path.exists(os.path.join(self.data_dir, file_names[0])):
                import_dir = self.data_dir

        for fname in file_names:
            fpath = os.path.join(import_dir, fname)
            if not os.path.exists(fpath):
                print(f"{YELLOW}Skipping missing file: {fname}{RESET}")
                continue

            print(f"{YELLOW}Processing {fpath}...{RESET}")

            # 1. Context sample for domain awareness
            context_sample = self._get_representative_sample(fpath)
            prompt_template = self._build_prompt_template(context_sample)
            print(f"{CYAN}  [debug] prompt_template length={len(prompt_template)}, "
                  f"has {{text}}={'{{text}}' in prompt_template}{RESET}")

            # 2. Pipeline
            print(f"{CYAN}  [debug] Creating SimpleKGPipeline...{RESET}")
            try:
                kg_builder = SimpleKGPipeline(
                    llm=self.llm_adapter,
                    driver=self.driver,
                    embedder=self.embedder_adapter,
                    from_pdf=True,
                    pdf_loader=MarkdownDataLoader(),
                    text_splitter=RegexTextSplitter(r"\n---\n"),
                    schema="FREE",
                    prompt_template=prompt_template,
                    on_error="RAISE",
                )
                print(f"{CYAN}  [debug] Pipeline created OK{RESET}")
            except Exception as e:
                print(f"{RED}  [debug] Pipeline creation FAILED: {e}{RESET}")
                traceback.print_exc()
                continue

            # 3. Execution
            try:
                print(f"{CYAN}  [debug] Running pipeline...{RESET}")
                result = await kg_builder.run_async(file_path=fpath)
                print(f"{GREEN}✓ Processed {fname}. Result: {result.result}{RESET}")
            except Exception as e:
                print(f"{RED}Error processing {fname}: {e}{RESET}")
                traceback.print_exc()

    def resolve_entities(self):
        """
        Performs Entity Resolution using Jaro-Winkler distance.
        Links extracted `__Entity__` nodes to Domain nodes (product, ingredient, etc.)
        """
        print(f"\n{CYAN}--- 🔗 Running Entity Resolution ---{RESET}")

        # 1. Find Unique Entity Labels (extracted nodes have `__Entity__` label)
        # We assume we want to link `__Entity__` nodes to Domain nodes (Product, Ingredient)

        labels_q = """
        MATCH (n) WHERE n:`__Entity__`
        WITH DISTINCT labels(n) AS lbls
        UNWIND lbls as l
        WITH l
        WHERE NOT l STARTS WITH "__"
        RETURN collect(distinct l) as unique_labels
        """
        res = graphdb.send_query(labels_q)
        if not res or not res[0].get('unique_labels'):
            print(f"{YELLOW}No extracted entities found to resolve.{RESET}")
            return

        labels = res[0]['unique_labels']
        print(f"Resolving Labels: {labels}")

        # 2. For each label, try to link to Domain nodes
        # We hardcode the match key 'name' for simplicity.
        # In a robust system, we would dynamically discover keys.

        threshold = 0.85
        distance_threshold = 1.0 - threshold

        for label in labels:
            print(f"Resolving {label}...")

            # Check if domain nodes exist
            check_q = f"MATCH (n:{label}) WHERE NOT n:`__Entity__` RETURN count(n) as c"
            check_res = graphdb.send_query(check_q)
            if check_res and check_res[0]['c'] == 0:
                print(f"  > No domain nodes for {label}, skipping.")
                continue

            # Run Jaro-Winkler Merge strategy
            # We assume property is 'name' or 'id'
            # Let's try 'name' -> 'name' mapping

            query = f"""
            MATCH (entity:{label}:`__Entity__`), (domain:{label})
            WHERE NOT domain:`__Entity__`
            AND entity.name IS NOT NULL AND domain.name IS NOT NULL
            AND apoc.text.jaroWinklerDistance(entity.name, domain.name) < {distance_threshold}
            MERGE (entity)-[r:CORRESPONDS_TO]->(domain)
            ON CREATE SET r.created_at = datetime(), r.score = 1.0 - apoc.text.jaroWinklerDistance(entity.name, domain.name)
            RETURN count(r) as connections
            """

            try:
                link_res = graphdb.send_query(query)
                count = link_res[0]['connections'] if link_res else 0
                if count > 0:
                    print(f"{GREEN}  > Linked {count} entities for {label}.{RESET}")
                else:
                    print(f"  > No matches found.")
            except Exception as e:
                print(f"{RED}  > Error resolving {label}: {e}{RESET}")

        self.log_extraction_stats()

    def log_extraction_stats(self):
        """Log all extracted entities to the build log."""
        # Use debug folder in base_path if possible
        log_path = os.path.join(self.data_dir, 'debug', 'graph_build_log.md')

        print(f"\n{CYAN}--- 📝 Logging Extracted Entities ---{RESET}")

        query = "MATCH (n:`__Entity__`) RETURN n"
        result = graphdb.send_query(query)

        count = len(result) if result else 0

        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a') as f:
                f.write(f"\n## Unstructured Extraction Results ({count} Entities)\n")
                if result:
                    for record in result:
                        node = record['n']
                        if hasattr(node, 'labels'):
                            lbls = list(node.labels)
                        else:
                            lbls = []

                        labels = ":".join([l for l in lbls if l != '__Entity__'])
                        props_dict = dict(node)
                        props = json.dumps(props_dict, default=str)
                        f.write(f"- (:{labels}) {props}\n")

            print(f"{GREEN}Logged {count} extracted entities to {log_path}{RESET}")
        except Exception as e:
            print(f"{RED}Failed to log stats: {e}{RESET}")
