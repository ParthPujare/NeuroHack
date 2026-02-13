# Sekhmet (NeuroHack)

A modular AI orchestration platform with long-term hybrid memory using FastAPI, Next.js, ChromaDB, Neo4j, and Groq/Gemini.

## Architecture

![Architecture Diagram](./architecture.md)

See [Architecture Documentation](architecture.md) for details on the system components and data flow.

## Prerequisites

- **Python 3.9+** (Required) - [Download Python](https://www.python.org/downloads/)
    - *Note for Windows: Use `python` or `py` if `python3` is not found.*
- **Node.js v18+** (Required) - [Download Node.js](https://nodejs.org/)
- **Neo4j Database** (Required for Graph Memory)
- **Supabase/PostgreSQL** (Required database)
- **LLM API Keys** (Groq, Google Gemini)

### Supabase/PostgreSQL Setup (Recommended)

To get the necessary database credentials for your `.env` file:

1.  Log in to your [Supabase Dashboard](https://supabase.com/dashboard/projects).
2.  Select your project.
3.  Click the **Connect** button at the top of the page.
4.  Navigate to **Connection String** tab.
5.  Select **Session Pooler** (preferred for high-performance applications).
6.  Change the **Mode** or **Type** to **Python** (instead of URI).
7.  Scroll down to see the individual parameters like `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`(.env->view parameters)
8.  Copy these values into your `.env` file during the installer setup or manually.

## Quick Setup (Recommended)

We provide an automated installation script to set up the backend, frontend, and environment variables.

1.  **Run the installer:**
    **Linux/Mac:**
    ```bash
    python3 install.py
    ```
    **Windows:**
    ```bash
    python install.py
    ```
    Follow the on-screen prompts to:
    - Choose your database type (**PostgreSQL**).
    - Configure your environment variables.
    - **Auto-Start**: The installer will offer to launch both servers for you!

2.  **Start the Backend:**
    **Linux/Mac:**
    ```bash
    source .venv/bin/activate
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    **Windows(Command prompt):**
    ```bash
    .venv\Scripts\activate
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    ```

3.  **Start the Frontend:**
    Open a new terminal:
    ```bash
    cd frontend
    npm run dev
    ```
    Access the app at `http://localhost:3000`.

## Accessing the App

Once both the backend and frontend are running, open your browser and navigate to:
**[http://localhost:3000](http://localhost:3000)**

## Manual Setup

If you prefer to set up manually:

1.  **Backend Setup:**
    **Linux/Mac:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    ```
    **Windows(Command prompt):**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    ```

2.  **Frontend Setup:**
    ```bash
    cd frontend
    npm install
    ```

## Environment Variables

The installer will prompt you for these, or you can set them in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | For Google Gemini API | - |
| `GROQ_API_KEY` | For Groq API (Llama 3) | - |
| `NEO4J_URI` | Neo4j Connection URI | - |
| `NEO4J_USER` | Neo4j Username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j Password | - |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL Details | - |

## Features

- **Hybrid Memory**: Combines semantic search (ChromaDB) with structured graph facts (Neo4j).
- **Planner Agent**: Intelligently decides when to search vector vs. graph memory.
- **Modern UI**: Next.js frontend with a chat interface and visualization.
- **Asynchronous Processing**: Background memory updates for performance.
