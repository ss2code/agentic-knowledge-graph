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
