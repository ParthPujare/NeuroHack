# Sekhmet (NeuroHack)

A modular AI orchestration platform with long-term hybrid memory using FastAPI, Next.js, ChromaDB, Neo4j, and Groq/Gemini.

## Architecture

![Architecture Diagram](./architecture.md)

See [Architecture Documentation](architecture.md) for details on the system components and data flow.

## Prerequisites

- **Python 3.9+** installed
- **Node.js v18+** installed
- **Neo4j Database** (Cloud or Desktop)
- **Supabase/PostgreSQL Database**
- **LLM API Keys** (Groq, Google Gemini)

## Quick Setup (Recommended)

We provide an automated installation script to set up the backend, frontend, and environment variables.

1.  **Run the installer:**
    ```bash
    python3 install.py
    ```
    Follow the on-screen prompts to configure your environment variables.

2.  **Start the Backend:**
    ```bash
    # Linux/Mac
    source .venv/bin/activate
    # Windows
    # .venv\Scripts\activate

    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    ```

3.  **Start the Frontend:**
    Open a new terminal:
    ```bash
    cd frontend
    npm run dev
    ```
    Access the app at `http://localhost:3000`.

## Manual Setup

If you prefer to set up manually:

1.  **Backend Setup:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    # Edit .env with your keys
    ```

2.  **Frontend Setup:**
    ```bash
    cd frontend
    npm install
    ```

## Environment Variables

The installer will prompt you for these, or you can set them in `.env`:

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | For Google Gemini API |
| `NEO4J_URI` | Neo4j Connection URI (e.g., neo4j+s://...) |
| `NEO4J_USER` | Neo4j Username (default: neo4j) |
| `NEO4J_PASSWORD` | Neo4j Password |
| `GROQ_API_KEY` | For Groq API (Llama 3) |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL Connection Details |

## Features

- **Hybrid Memory**: Combines semantic search (ChromaDB) with structured graph facts (Neo4j).
- **Planner Agent**: Intelligently decides when to search vector vs. graph memory.
- **Modern UI**: Next.js frontend with a chat interface and visualization.
- **Asynchronous Processing**: Background memory updates for performance.
