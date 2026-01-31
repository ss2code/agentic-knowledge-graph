#!/bin/bash
echo "Stopping old container..."
docker stop neo4j-apoc
docker rm neo4j-apoc

echo "Pulling latest Neo4j image..."
docker pull neo4j:latest

echo "Starting new Neo4j container..."
docker run -d \
    --name neo4j-apoc \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS='["apoc"]' \
    -e NEO4J_apoc_export_file_enabled=true \
    -e NEO4J_apoc_import_file_enabled=true \
    -e NEO4J_apoc_import_file_use__neo4j__config=true \
    -e NEO4J_dbms_security_procedures_unrestricted=apoc.* \
    -v $PWD/data/user_data:/var/lib/neo4j/import \
    -v neo4j_data:/data \
    -v neo4j_logs:/logs \
    neo4j:latest

echo "Waiting for Neo4j to start..."
sleep 10
echo "Done! Please verify access at http://localhost:7474"
