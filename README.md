# Hybrid Memory RAG

A conversational AI with long-term hybrid memory using FastAPI, Streamlit, ChromaDB, Neo4j, and Google Gemini.

## Prerequisites

- **Python 3.10+** installed
- **Neo4j Desktop** installed and running (optional, but recommended for full graph features)
- **Google Gemini API Key** obtained from AI Studio

## Setup

1.  **Clone/Navigate to the project directory:**
    ```bash
    cd /Users/parth/Documents/Work/Hackathons/NeuroHack
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    - Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    - Open `.env` and fill in your `GOOGLE_API_KEY`, `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`.

## Running the Application

You need to run the **Backend** and **Frontend** in separate terminals.

### Terminal 1: Backend (FastAPI)

Start the API server on port 8000:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend (Streamlit)

Start the chat interface on port 8501:

```bash
streamlit run frontend/app.py
```

## Features

- **Hybrid Retrieval**: Combines semantic search (ChromaDB) with structured graph facts (Neo4j).
- **Planner Agent**: Intelligently decides when to search vector vs. graph memory.
- **Asynchronous Updates**: Memory updates happen in the background to keep the UI responsive.
- **Robust Error Handling**: Gracefully handles API rate limits and connection issues.
