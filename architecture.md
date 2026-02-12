# System Architecture

## Overview
Sekhmet is a modular AI orchestration platform that integrates multiple LLMs, a graph database for long-term memory, and a modern web interface.

## Tech Stack
- **Frontend**: Next.js 15 (React 19), TailwindCSS, Framer Motion
- **Backend**: Python (FastAPI/Uvicorn)
- **AI Models**: Groq (Llama 3), Google Gemini
- **Memory/Database**: 
  - **Neo4j**: Graph database for structured long-term memory (Entities, Facts, Preferences)
  - **Chroma**: Vector database for semantic search
  - **PostgreSQL**: Relational data (users, chat logs)

## Architecture Diagram

```mermaid
graph TD
    User[User] -->|Browser| FE[Next.js Frontend]
    FE -->|HTTP API| BE[Python Backend (FastAPI)]
    
    subgraph "Backend System"
        BE -->|Orchestrate| Pipeline[Pipeline Manager]
        Pipeline -->|Planning| Planner[Planner Agent (Groq)]
        Pipeline -->|Retrieval| Memory[Memory Manager]
        Pipeline -->|Synthesis| Synthesizer[Synthesizer Agent (Gemini/Groq)]
    end
    
    subgraph "Data Layer"
        Memory <-->|Structured Data| Neo4j[(Neo4j Graph DB)]
        Memory <-->|Semantic Data| Chroma[(Chroma Vector DB)]
        BE <-->|User Data| Postgres[(PostgreSQL)]
    end
    
    subgraph "External AI Services"
        Planner -.->|API Call| GroqAPI[Groq API]
        Synthesizer -.->|API Call| GeminiAPI[Google Gemini API]
    end
```

## Data Flow
1. **Input**: User sends a message via the Frontend.
2. **Processing**: Backend receives the message and initiates the `Pipeline`.
3. **Planning**: The Planner agent analyzes the intent and decides what memory or tools are needed.
4. **Retrieval**: System fetches relevant context from Neo4j (Graph) and Chroma (Vector).
5. **Synthesis**: The Synthesizer agent combines the user message, retrieved context, and system instructions to generate a response.
6. **Memory Update**: The interaction is asynchronously analyzed to update the graph and vector memory with new facts or preferences.
7. **Output**: The response is sent back to the Frontend.
