import os
import shutil
from neo4j import GraphDatabase
import time

# Use colors for CLI output (reused from orchestrator)
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

class GraphService:
    """
    Singleton service for managing Neo4j connections and query execution.
    """
    def __init__(self, uri=None, auth=None):
        """
        Initialize the Graph Service.

        Args:
            uri (str): Neo4j Bolt URI. Defaults to env param or localhost.
            auth (tuple): (username, password). Defaults to env param or neo4j/password.
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.auth = auth or (
            os.getenv("NEO4J_USERNAME", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "password")
        )
        self.driver = None

    def connect(self):
        if not self.driver:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
                # Verify connectivity
                self.driver.verify_connectivity()
                return True
            except Exception as e:
                # print(f"{RED}Neo4j Connection Failed: {e}{RESET}") # Be silent on initial check
                return False
        return True

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    def import_graph(self, filename):
        """Imports graph from a GraphML file using APOC."""
        if not self.connect(): return False
        
        # filename should be relative to import dir
        # We assume the caller has placed the file in the import dir
        import_query = f"CALL apoc.import.graphml('{filename}', {{readLabels: true}})"
        
        print(f"{YELLOW}>> Importing graph from {filename} (in container)...{RESET}")
        try:
            res = self.send_query(import_query)
            return True
        except Exception as e:
             print(f"{RED}Import failed: {e}{RESET}")
             return False

    def get_schema_visualization(self):
        """
        Retrieves the meta-graph schema using APOC and transforms it into 
        a simplified JSON structure for LLM consumption.
        """
        if not self.connect(): return None
        
        query = "CALL apoc.meta.graph"
        try:
            # apoc.meta.graph returns a set of nodes and relationships that represent the schema
            # We need to extract the labels/types and properties from this result.
            # However, apoc.meta.graph returns actual graph objects (nodes/rels).
            # A easier way for LLM might be apoc.meta.schema, but let's stick to the prompt.
            # Actually, standard apoc.meta.graph returns:
            # nodes: [list of nodes representing labels], relationships: [list of relationships]
            
            # Let's try apoc.meta.schema or apoc.meta.data for easier parsing if available,
            # but usually meta.graph is standard.
            
            # Alternative: Construct a JSON manually from `CALL apoc.meta.schema()` if available
            # or simply use the provided query in standard prompt suggestions.
            
            # Let's stick to a robust manual query that mimics meta-graph but returns JSON directly
            # or just use the apoc.meta.graph and parse it.
            
            # Simplest for LLM:
            schema_query = """
            CALL apoc.meta.schema() YIELD value
            RETURN value
            """
            # If apoc.meta.schema is not available/complex, let's use:
            # CALL apoc.meta.data()
            
            # Let's implement a robust custom schema query that is purely Cypher if APOC is tricky,
            # BUT the user asked for APOC.
            
            # Using apoc.meta.graph involves parsing the graph result which is complex in python driver
            # (receiving Node/Relationship objects).
            # `apoc.meta.data` yields a table.
            
            # Let's use `apoc.meta.schema` as it returns a nice map.
            res = self.send_query(schema_query)
            if res and 'value' in res[0]:
                return res[0]['value']
                
            # Fallback if that returns empty (sometimes happens)
            return self.send_query("CALL apoc.meta.data()")
            
        except Exception as e:
            print(f"{RED}Schema Extraction Failed: {e}{RESET}")
            return None

    def validate_cypher(self, cypher):
        """
        Validates Cypher syntax using EXPLAIN.
        Returns (is_valid, error_message).
        """
        if not self.connect(): return False, "No Connection"
        
        try:
            with self.driver.session() as session:
                # EXPLAIN query prevents execution but checks syntax
                session.run(f"EXPLAIN {cypher}")
                return True, None
        except Exception as e:
            return False, str(e)


    def send_query(self, cypher, params=None):
        """Execute a Cypher query and return results as a list of dicts."""
        if not self.connect():
            return None
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, params or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"{RED}Query Failed: {e}{RESET}")
            print(f"{YELLOW}Query: {cypher}{RESET}")
            return {"status": "error", "message": str(e)}

    def nuke_database(self):
        """Dangerous: Clears the entire database."""
        return self.send_query("MATCH (n) DETACH DELETE n")

    def export_graph(self, filename):
        """Exports graph to a GraphML file using APOC."""
        if not self.connect(): return False
        
        # We export to the import folder because Neo4j can write there easily
        # filename should be relative to import dir, e.g. "graph_dump.graphml"
        export_query = f"CALL apoc.export.graphml.all('{filename}', {{}})"
        
        print(f"{YELLOW}>> Exporting graph to {filename} (in container)...{RESET}")
        try:
            res = self.send_query(export_query)
            # APOC returns a stream or result, check for error in result dict
            return True
        except Exception as e:
             print(f"{RED}Export failed: {e}{RESET}")
             return False

# Singleton instance for easy import
graphdb = GraphService()
