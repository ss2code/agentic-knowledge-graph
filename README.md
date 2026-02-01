# Agentic Knowledge Graph Orchestrator

This project provides an agent-based system for building, refining, and visualizing Knowledge Graphs from structured and unstructured data.

> **Attribution**: This is an implementation using Antigravity IDE and Google AI Studio. It follows the [Agentic Knowledge Graph Construction](https://learn.deeplearning.ai/courses/agentic-knowledge-graph-construction/) course from DeepLearning.AI. (Please do not delete this attribution).

## 🐣 Quick Start

### Prerequisites
1.  **Install Python 3.10+** from [python.org](https://www.python.org/downloads/).
2.  **Install Docker Desktop** from [docker.com](https://www.docker.com/products/docker-desktop/) and ensure it is running (`docker info` should work).
3.  **Get a Gemini API Key** from [aistudio.google.com](https://aistudio.google.com/app/apikey).

### Setup (Step-by-Step)
1.  **Open your Terminal** (or Command Prompt).
2.  **Navigate to the project folder**:
    ```bash
    cd /path/to/project
    ```
3.  **Create a Virtual Environment** (isolates your dependencies):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    # On Windows: .venv\Scripts\activate
    ```
4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Set your API Key** (Optional, you can also enter it when prompted):
    ```bash
    export GEMINI_API_KEY="your_api_key_here"
    ```

### Running the App
Run the orchestrator in interactive mode:
```bash
python3 orchestrator.py
```

## 📂 Context Separation (Recommended)
To keep your data organized and separate from the code, use **Context Directories**.

Run with a specific context path:
```bash
python3 orchestrator.py --context /Users/me/Documents/My_KG_Project
```
The application will automatically create the necessary folders in that path:
- `user_data/`: **PUT YOUR INPUT FILES HERE** (CSV, TXT, MD).
- `debug/`: Check here for **LLM Logs** (`debug_llm_*.md`) to see exactly what the AI is sending/receiving.
- `neo4j_home/`: Database files (managed automatically).
- `output/`: Visualizations and Data Dumps.

## 📂 Project Structure (Best Practice)

We recommend organizing your data into "Context" directories. A Context directory should look like this:

```text
/Users/username/Documents/My_KG_Project/   <-- Context Root
├── user_data/                             <-- PUT YOUR INPUT FILES HERE (CSV, TXT, MD)
├── neo4j_home/                            <-- Auto-generated (Database storage & logs)
└── output/                                <-- Auto-generated (Visualizations & Reports)
```

The application will **automatically create** `neo4j_home` and `output` if they don't exist. You only need to create the `user_data` folder and drop your files in it.

## 🧠 Orchestrator Structure

The **Orchestrator** (`orchestrator.py`) acts as the central nervous system of the application, coordinating agents and services to transform raw data into a Knowledge Graph.

**Core Responsibilities:**
*   **Context Management**: Ensures data isolation by managing project-specific directories (`user_data`, `neo4j_home`, `output`).
*   **State Management**: Tracks the project lifecycle using `StateManager`, ensuring step-by-step execution intent -> schema -> extraction -> build.
*   **Agent Coordination**: Sequentially invokes specialized agents (Intent, Schema, Extraction, Graph Builder, Visualizer).
*   **Infrastructure Control**: Automatically spins up and manages Neo4j Docker containers for each context.

**Usage Summary & Workflow Options:**
Run `python3 orchestrator.py` to enter the interactive main loop. The options guide you through the lifecycle:

1.  **Define Intent**: Interactive interview with the `IntentAgent` to establish your goals and domain.
2.  **Review Contract**: helper to view the generated `user_intent.json`.
3.  **Approve Files**: Scans `user_data/`, lists found files, and locks them for processing.
4.  **Negotiate Schema**: `SchemaRefinementLoop` iteratively designs the Graph Schema (Nodes/Relationships).
5.  **Design Extraction Logic**: `ExtractionSchemaLoop` generates the mapping plan from raw files -> Schema.
6.  **Build/Refresh Graph**: `GraphBuilderAgent` executes the extraction and populates Neo4j.
7.  **Run Knowledge Discovery**: Runs GraphRAG pipeline on unstructured text (MD/TXT) to finding entities/connections.
8.  **Inspect Graph Stats**: Quick check of node counts and recent entries in the DB.
9.  **Load Dump & Visualize**: Loads an exported `.graphml` into Neo4j and launches the web visualizer.
10. **Export Data Dump**: Snapshots the current database to a `.graphml` file in `output/`.
11. **Clean Up Context**: Dangerous reset – deletes the DB container and generated config files.
12. **Text-to-Cypher Interface**: Chat with your data using natural language queries.

## 🛠 CLI Commands

You can automate tasks using the CLI mode:

### Build Graph
```bash
python3 orchestrator.py --context /path/to/my_project --cli --action build
```

### Visualize
```bash
python3 orchestrator.py --context /path/to/my_project --cli --action visualize
```

### Export Data
```bash
python3 orchestrator.py --context /path/to/my_project --cli --action export
```

## 🐳 Docker Management

The orchestrator automatically manages a Docker container for each context to ensure isolation.
- Context: `My_KG_Project` -> Container: `neo4j-My_KG_Project`
- Ports: Default `7474` and `7687`. *Note: Currently, multiple contexts cannot run simultaneously on the same ports.*

## 🔑 Environment Variables

Create a `.env` file or export:
```bash
export GEMINI_API_KEY="your_api_key"
```
