from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.memory_manager import MemoryManager
from backend.pipeline import Pipeline
from backend.models import ChatRequest, ChatResponse
from backend.database import get_db_connection
import uvicorn
import json
import uuid

# Global instances
memory_manager = None
pipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global memory_manager, pipeline
    print("Initializing memory manager...")
    memory_manager = MemoryManager()
    pipeline = Pipeline(memory_manager)
    
    print("Initializing Database Pool...")
    from backend.database import init_pool, close_pool, init_db
    await init_pool()
    await init_db()
    
    yield
    # Shutdown
    print("Closing memory manager...")
    if memory_manager:
        memory_manager.close()
    
    print("Closing Database Pool...")
    await close_pool()

app = FastAPI(lifespan=lifespan)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now, or specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    # Process turn (Steps 1-5)
    response = await pipeline.process_turn(request.message, request.user_id, request.conversation_id)
    
    # Schedule Async Update (Step 6)
    background_tasks.add_task(
        pipeline.run_async_update, 
        request.message, 
        response.response, 
        request.user_id,
        response.step_logs.get('step2_retrieval') if response and response.step_logs else None
    )
    
    return response

@app.get("/user")
async def get_user():
    # Simple user ID generation/retrieval
    # In a real app, this would be handled by auth
    return {"user_id": "user_12345"}

@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str):
    try:
        async with await get_db_connection() as conn:
            rows = await conn.fetch('''
                SELECT id, title, created_at, updated_at 
                FROM conversations 
                WHERE user_id = $1 
                ORDER BY updated_at DESC
            ''', user_id)
            return [dict(row) for row in rows]
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database is not available")

@app.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    try:
        async with await get_db_connection() as conn:
            rows = await conn.fetch('''
                SELECT role, content, created_at 
                FROM messages 
                WHERE conversation_id = $1 
                ORDER BY created_at ASC
            ''', conversation_id)
            return [dict(row) for row in rows]
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database is not available")

@app.post("/conversations")
async def create_conversation(request: dict):
    try:
        user_id = request.get("user_id")
        title = request.get("title", "New Chat")
        async with await get_db_connection() as conn:
            conversation_id = await conn.fetchval('''
                INSERT INTO conversations (user_id, title) 
                VALUES ($1, $2) 
                RETURNING id
            ''', user_id, title)
            return {"id": str(conversation_id), "title": title}
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database is not available")

@app.patch("/conversations/{conversation_id}")
async def update_conversation_title(conversation_id: str, request: dict):
    try:
        title = request.get("title")
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
            
        async with await get_db_connection() as conn:
            await conn.execute('UPDATE conversations SET title = $1 WHERE id = $2', title, conversation_id)
            return {"id": conversation_id, "title": title}
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database is not available")

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    try:
        async with await get_db_connection() as conn:
            await conn.execute('DELETE FROM conversations WHERE id = $1', conversation_id)
            return {"status": "success"}
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database is not available")

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
