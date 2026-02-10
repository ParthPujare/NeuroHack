import os
import json
import asyncio
from backend.memory_manager import MemoryManager
from backend.models import ChatResponse
from backend.llm_factory import LLMFactory

class Pipeline:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        
        # Initialize Dual-LLM System
        print("Initializing Dual-LLM System...")
        self.local_llm = LLMFactory.get_provider("llama_local")
        self.remote_llm = LLMFactory.get_provider("gemini")
        print("Dual-LLM System Ready.")

    async def process_turn(self, user_message: str, user_id: str) -> ChatResponse:
        logs = {}
        try:
            # --- Step 1: Planner (Intent Extraction) - Local LLM ---
            planner_prompt = f"""
            Analyze the following user message: "{user_message}"
            Identify core entities and generate search terms for a vector database and a Cypher query for a graph database (Neo4j).
            The user ID is '{user_id}'.
            
            Output a JSON object with:
            - entities: list of strings
            - search_terms: list of strings for semantic search
            - cypher_query: string (optional, null if no graph lookup needed). Use the label 'User' for the user.
            """
            
            # Use Local LLM for planning
            planner_response = await asyncio.to_thread(self.local_llm.generate_json, planner_prompt)
            logs['step1_planner'] = planner_response
            
            # --- Step 2: Retrieval ---
            # Vector Search (ChromaDB)
            vector_results = []
            if planner_response.get('search_terms'):
                for term in planner_response['search_terms']:
                    res = self.memory_manager.search_vector_memory(term)
                    if res and res['documents']:
                        vector_results.extend([doc for sublist in res['documents'] for doc in sublist])
            
            # Graph Search (Neo4j)
            graph_results = []
            if planner_response.get('cypher_query'):
                try:
                    graph_results = self.memory_manager.run_graph_query(planner_response['cypher_query'])
                except Exception as e:
                    print(f"Graph query failed: {e}")
                    logs['step2_graph_error'] = str(e)

            logs['step2_retrieval'] = {
                'vector': vector_results,
                'graph': graph_results
            }

            # --- Step 3: Reconciliation (Logic) ---
            context_str = f"Semantic Memory:\n{vector_results}\n\nStructured Memory:\n{graph_results}"
            logs['step3_reconciliation'] = context_str

            # --- Step 4: Synthesis - Local LLM ---
            synthesis_prompt = f"""
            Synthesize the following memory context into a coherent narrative relevant to the user's current message: "{user_message}"
            
            Context:
            {context_str}
            
            If the context is empty or irrelevant, simply state "No relevant past context found."
            """
            synthesis_response = await asyncio.to_thread(self.local_llm.generate_text, synthesis_prompt)
            logs['step4_synthesis'] = synthesis_response

            # --- Step 5: Response - Remote LLM (Gemini) ---
            response_prompt = f"""
            You are a helpful AI assistant.
            User Message: "{user_message}"
            
            relevant Context (from memory):
            {synthesis_response}
            
            Generate a natural, helpful response.
            """
            final_response = await asyncio.to_thread(self.remote_llm.generate_text, response_prompt)
            
            return ChatResponse(
                response=final_response,
                context_used=synthesis_response,
                step_logs=logs
            )
        except Exception as e:
            print(f"Pipeline Error: {e}")
            import traceback
            traceback.print_exc()
            return ChatResponse(
                response="I'm currently experiencing system issues. Please try again in a moment.",
                context_used="Error during processing.",
                step_logs={"error": str(e), "partial_logs": logs}
            )

    async def run_async_update(self, user_message: str, assistant_response: str, user_id: str):
        """Step 6 implementation: Embed turn and update Neo4j using Local LLM."""
        print("Running async update...")
        
        # 1. Embed conversation turn
        turn_text = f"User: {user_message}\nAssistant: {assistant_response}"
        import time
        turn_id = f"turn_{int(time.time()*1000)}"
        
        self.memory_manager.add_vector_memory(turn_id, turn_text, metadata={"user_id": user_id, "timestamp": time.time()})
        
        # 2. Extract and Update Graph - Local LLM
        extraction_prompt = f"""
        Extract structured facts from this conversation interaction for a Neo4j graph database.
        User: "{user_message}"
        Assistant: "{assistant_response}"
        User ID: "{user_id}"
        
        Output a JSON object with:
        - nodes: list of objects {{"label": "...", "id": "...", "properties": {{...}}}}
        - relationships: list of objects {{"source_label": "...", "source_id": "...", "target_label": "...", "target_id": "...", "type": "...", "properties": {{...}}}}
        
        Focus on user preferences, events, and factual statements. MERGE strategy will be used, so ensure IDs are consistent (e.g., user_1 for the user).
        """
        
        try:
            updates = await asyncio.to_thread(self.local_llm.generate_json, extraction_prompt)
            print(f"DEBUG: Async Update JSON: {json.dumps(updates, indent=2)}")
            
            if updates.get('nodes'):
                for node in updates['nodes']:
                    print(f"DEBUG: Adding node: {node}")
                    self.memory_manager.add_graph_node(node['label'], node['properties'])
            
            if updates.get('relationships'):
                for rel in updates['relationships']:
                    print(f"DEBUG: Adding rel: {rel}")
                    self.memory_manager.create_relationship(
                        rel['source_label'], rel['source_id'],
                        rel['type'],
                        rel['target_label'], rel['target_id'],
                        rel.get('properties', {})
                    )
            print("Async update completed.")
        except Exception as e:
            print(f"Async update failed: {e}")
            import traceback
            traceback.print_exc()
