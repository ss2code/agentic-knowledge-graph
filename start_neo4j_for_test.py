from core.context import Context
from services.container_service import ContainerService
import os

def start_neo4j():
    ctx = Context.from_path("data") # Default context
    svc = ContainerService(ctx)
    if not svc.is_running():
        print("Starting Neo4j...")
        svc.start_container()
    else:
        print("Neo4j is already running.")

if __name__ == "__main__":
    start_neo4j()
