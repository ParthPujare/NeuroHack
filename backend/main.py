from fastapi import FastAPI, BackgroundTasks, HTTPException
from contextlib import asynccontextmanager
from backend.memory_manager import MemoryManager
from backend.pipeline import Pipeline
from backend.models import ChatRequest, ChatResponse
import uvicorn

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
    yield
    # Shutdown
    print("Closing memory manager...")
    if memory_manager:
        memory_manager.close()

app = FastAPI(lifespan=lifespan)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    # Process turn (Steps 1-5)
    response = await pipeline.process_turn(request.message, request.user_id)
    
    # Schedule Async Update (Step 6)
    background_tasks.add_task(
        pipeline.run_async_update, 
        request.message, 
        response.response, 
        request.user_id,
        response.step_logs.get('step2_retrieval') if response and response.step_logs else None
    )
    
    return response

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
