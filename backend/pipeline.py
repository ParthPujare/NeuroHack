import os
import json
import asyncio
from backend.memory_manager import MemoryManager
from backend.models import ChatResponse
from backend.llm_factory import LLMFactory, LLMProvider
import difflib
from difflib import SequenceMatcher

class Pipeline:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        
        # Initialize LLM System
        print("Initializing LLM System...")
        
        force_local = os.getenv("FORCE_LOCAL", "false").lower() == "true"
        
        if force_local:
            print("FORCE_LOCAL=true: Attempting to load Local LLM...")
            try:
                self.fast_llm = LLMFactory.get_provider("llama_local")
                self.use_local_llm = True
                print("✓ Local LLM (Llama) loaded successfully")
            except (ImportError, Exception) as e:
                print(f"⚠ Local LLM unavailable ({e}). Falling back to Groq.")
                self.fast_llm = LLMFactory.get_provider("groq")
                self.use_local_llm = False
        else:
            print("FORCE_LOCAL=false: Using Groq (Cloud Llama)...")
            self.fast_llm = LLMFactory.get_provider("groq")
            self.use_local_llm = False # distinct flag if logic depends on it, but here we just want the provider
        
        # Keep Gemini for now as remote_llm (or should this also be Groq? User only said replace context agent and default to Groq)
        # However, the user said "replace the agent that handles the context add/buildup... instead of gemini"
        # And "by default it will use the cloud groq llama" (referring to local replacement).
        # Let's assume remote_llm (Gemini) stays for now unless specified otherwise, 
        # BUT current pipeline uses `llm_to_use` which switches between local and remote.
        
        self.remote_llm = LLMFactory.get_provider("gemini")
        print("✓ Remote LLM (Gemini) ready")
        print("LLM System Ready.")

    def _deduplicate_results(self, results: list, threshold: float = 0.85) -> list:
        """
        Deduplicates semantic search results based on sequence similarity.
        Keep results that are distinct enough (similarity < threshold).
        results: list of dicts {'id': ..., 'content': ...}
        """
        unique_results = []
        for new_item in results:
            is_duplicate = False
            for existing_item in unique_results:
                # Calculate similarity ratio
                similarity = SequenceMatcher(None, new_item['content'], existing_item['content']).ratio()
                if similarity > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(new_item)
        
        return unique_results

    async def process_turn(self, user_message: str, user_id: str) -> ChatResponse:
        logs = {}
        try:
            # Determine which LLM to use
            # If force_local was true and loaded, use it. Else use Groq (fast_llm).
            # If fast_llm failed to load (unlikely for Groq unless API key missing), fallback to remote.
            
            llm_to_use = self.fast_llm if self.fast_llm else self.remote_llm

            # --- Step 0: Temporal Context Planner ---
            temporal_planner_prompt = f"""
            Analyze the user message for any overrides or updates to previous preferences or schedules.
            User Message: "{user_message}"
            
            Task:
            1. Is the user correcting or updating something they might have said before? (e.g., "instead", "wait", "actually", "change to")
            2. Identify the target entity type (User, Preference, Event).
            
            Output JSON:
            {{
                "is_override": boolean,
                "target_node_label": "User|Preference|Event|null",
                "conflict_summary": "string|null"
            }}
            """
            temporal_check = await asyncio.to_thread(llm_to_use.generate_json, temporal_planner_prompt)
            logs['step0_temporal_check'] = temporal_check
            logs['step0_temporal_check']['model'] = llm_to_use.provider_name
            logs['step0_temporal_check']['prompt'] = temporal_planner_prompt
            if temporal_check.get('is_override'):
                print(f"DEBUG: Temporal Conflict Detected: {temporal_check['conflict_summary']}")

            # --- Step 1: Planner (Intent Extraction) ---
            planner_prompt = f"""
            Analyze the following user message: "{user_message}"
            Identify core entities and generate search terms for a vector database and a Cypher query for a graph database (Neo4j).
            
            Context:
            - User ID: '{user_id}'
            - Override Detected: {temporal_check.get('is_override')}
            - Target: {temporal_check.get('target_node_label')}
            
            Schemas:
            - User {{id, name}}
            - Preference {{name, value, status}}
            - Fact {{description, value, status}}
            - Entity {{name, type, status}}
            - Constraint {{name, description, status}}
            - Commitment {{description, due_date, status}}
            - Instruction {{description, priority, status}}
            
            Instructions:
            1. Query for ACTIVE nodes only (status: 'active').
            2. If an override was detected, prioritize searching for the existing version of that preference/entity.
            3. Retrieve ALL relevant constraints, preferences, and facts for the user.
            
            Output JSON with search_terms (list), cypher_query (string) and needs_search (boolean).
            Example Query: 
            MATCH (u:User {{id: '{user_id}'}})
            OPTIONAL MATCH (u)-[:HAS_PREFERENCE]->(p:Preference {{status: 'active'}})
            OPTIONAL MATCH (u)-[:HAS_CONSTRAINT]->(c:Constraint {{status: 'active'}})
            OPTIONAL MATCH (u)-[:HAS_FACT]->(f:Fact {{status: 'active'}})
            RETURN p, c, f
            """
            
            planner_response = await asyncio.to_thread(llm_to_use.generate_json, planner_prompt)
            print(f"DEBUG: Raw Planner Response: {json.dumps(planner_response, indent=2)}")
            logs['step1_planner'] = planner_response
            logs['step1_planner']['model'] = llm_to_use.provider_name
            logs['step1_planner']['prompt'] = planner_prompt
            
            # --- Step 2: Retrieval ---
            # Ensure User node exists first
            self.memory_manager.ensure_user_exists(user_id)
            
            # Vector Search (ChromaDB)
            vector_results = []
            seen_vector_ids = set()
            
            if planner_response.get('search_terms'):
                for term in planner_response['search_terms']:
                    res = self.memory_manager.search_vector_memory(term, n_results=5)
                    if res and res['documents'] and res['ids']:
                        for i, list_of_docs in enumerate(res['documents']):
                            list_of_ids = res['ids'][i]
                            for j, doc in enumerate(list_of_docs):
                                doc_id = list_of_ids[j]
                                
                                # 1. ID-based Deduplication
                                if doc_id in seen_vector_ids:
                                    continue
                                    
                                # 2. Content-based Deduplication (Fuzzy Match)
                                is_duplicate = False
                                for existing in vector_results:
                                    existing_content = existing['content']
                                    similarity = SequenceMatcher(None, doc, existing_content).ratio()
                                    if similarity > 0.85: # 85% similarity threshold
                                        is_duplicate = True
                                        break
                                
                                if not is_duplicate:
                                    vector_results.append({'id': doc_id, 'content': doc})
                                    seen_vector_ids.add(doc_id)
            
            # Fuzzy Deduplication (remove near-duplicates like similar code chunks)
            vector_results = self._deduplicate_results(vector_results, threshold=0.85)
            
            # Limit to top 10 unique results related to query
            vector_results = vector_results[:10]
            
            # Graph Search (Neo4j) - ALWAYS retrieve ALL active nodes for the user
            # This ensures turn 1 information is available at turn 1000
            graph_results = []
            try:
                # Use comprehensive query to get ALL 6 node types
                comprehensive_query = f"""
                MATCH (u:User {{id: '{user_id}'}})
                OPTIONAL MATCH (u)-[:HAS_PREFERENCE]->(pref:Preference {{status: 'active'}})
                OPTIONAL MATCH (u)-[:HAS_FACT]->(fact:Fact {{status: 'active'}})
                OPTIONAL MATCH (u)-[:HAS_ENTITY]->(entity:Entity {{status: 'active'}})
                OPTIONAL MATCH (u)-[:HAS_CONSTRAINT]->(constraint:Constraint {{status: 'active'}})
                OPTIONAL MATCH (u)-[:HAS_COMMITMENT]->(commitment:Commitment {{status: 'active'}})
                OPTIONAL MATCH (u)-[:HAS_INSTRUCTION]->(instruction:Instruction {{status: 'active'}})
                RETURN 
                    collect(DISTINCT pref) as preferences,
                    collect(DISTINCT fact) as facts,
                    collect(DISTINCT entity) as entities,
                    collect(DISTINCT constraint) as constraints,
                    collect(DISTINCT commitment) as commitments,
                    collect(DISTINCT instruction) as instructions
                """
                print(f"DEBUG: Comprehensive Cypher Query: {comprehensive_query}")
                graph_results = self.memory_manager.run_graph_query(comprehensive_query)
                print(f"DEBUG: Graph Results: {graph_results}")
            except Exception as e:
                print(f"Graph query failed: {e}")
                logs['step2_graph_error'] = str(e)

            logs['step2_retrieval'] = {
                'vector': vector_results,
                'graph': graph_results,
                'search_terms': planner_response.get('search_terms'),
                'cypher_query': 'comprehensive_user_knowledge_query'
            }

            # --- Step 3: Reasoning & De-confliction ---
            # Structure the graph results by node type (from comprehensive query)
            structured_graph = {
                'preferences': [],
                'facts': [],
                'entities': [],
                'constraints': [],
                'commitments': [],
                'instructions': []
            }
            
            if graph_results and len(graph_results) > 0:
                result = graph_results[0]  # First row contains all collected nodes
                for key in structured_graph.keys():
                    nodes = result.get(key, [])
                    # Filter out None values and ensure only active nodes
                    structured_graph[key] = [
                        node for node in nodes 
                        if node and isinstance(node, dict) and node.get('status') != 'obsolete'
                    ]
            
            # Build structured context for LLM
            def format_nodes(nodes, node_type):
                """Format nodes for display with all relevant fields."""
                if not nodes:
                    return f"  No {node_type} recorded."
                formatted = []
                for node in nodes:
                    if node_type == 'Preferences':
                        name = node.get('name', 'Unknown')
                        value = node.get('value', 'N/A')
                        formatted.append(f"  • {name}: {value}")
                    
                    elif node_type == 'Facts':
                        # Primary: 'statement' field
                        if 'statement' in node:
                            formatted.append(f"  • {node['statement']}")
                        # Fallback: 'description' + 'value' fields
                        elif 'description' in node:
                            desc = node['description']
                            val = node.get('value', '')
                            formatted.append(f"  • {desc}: {val}" if val else f"  • {desc}")
                        # Last resort: show name or give up
                        else:
                            formatted.append(f"  • {node.get('name', str(node))}")
                    
                    elif node_type == 'Entities':
                        name = node.get('name', 'Unknown')
                        entity_type = node.get('type', 'unknown type')
                        context = node.get('context', '')
                        if context:
                            formatted.append(f"  • {name} ({entity_type}) - {context}")
                        else:
                            formatted.append(f"  • {name} ({entity_type})")
                    
                    elif node_type == 'Constraints':
                        name = node.get('name', 'Unknown')
                        description = node.get('description', 'N/A')
                        formatted.append(f"  • {name}: {description}")
                    
                    elif node_type == 'Commitments':
                        description = node.get('description', 'N/A')
                        due_date = node.get('due_date', 'Not set')
                        if due_date and due_date != 'Not set':
                            formatted.append(f"  • {description} [Due: {due_date}]")
                        else:
                            formatted.append(f"  • {description}")
                    
                    elif node_type == 'Instructions':
                        description = node.get('description', 'N/A')
                        priority = node.get('priority', 'normal')
                
                return '\n'.join(formatted)
            
            context_str = f"""
=== USER LONG-TERM MEMORY (Graph Database) ===
This information persists across ALL conversations and MUST influence your responses.

📋 PREFERENCES (How user likes things):
{format_nodes(structured_graph['preferences'], 'Preferences')}

📊 FACTS (Known information about user):
{format_nodes(structured_graph['facts'], 'Facts')}

🔖 ENTITIES (People, places, things user mentioned):
{format_nodes(structured_graph['entities'], 'Entities')}

🚫 CONSTRAINTS (Hard rules user set):
{format_nodes(structured_graph['constraints'], 'Constraints')}

✓ COMMITMENTS (What you promised to do):
{format_nodes(structured_graph['commitments'], 'Commitments')}

📝 INSTRUCTIONS (Long-term behavior modifications):
{format_nodes(structured_graph['instructions'], 'Instructions')}

=== SEMANTIC MEMORY (Recent Context) ===
=== SEMANTIC MEMORY (Recent Context) ===
{chr(10).join([f'  • {item["content"]}' for item in vector_results]) if vector_results else '  No recent semantic context.'}
            """
            logs['step3_reconciliation'] = {
                "content": context_str,
                "model": "Rules Based (Python)"
            }

            if self.fast_llm:
                # --- Step 4: Synthesis (Context Distillation) ---
                # Goal: Produce a SHORT context brief, NOT a full response
                synthesis_prompt = f"""
                You are a Context Distiller. Your ONLY job is to output a short bullet-point summary of relevant context for another AI to use when responding.
                
                User Message: "{user_message}"
                
                Memory Snapshot:
                {context_str}
                
                OUTPUT RULES:
                - Output ONLY a short bullet-point list of facts relevant to the user's current message and relevant preferences,facts.
                - DO NOT answer the user's question yourself
                - DO NOT generate code, explanations, or any response content
                - DO NOT analyze or reason about the context
                - Keep it under 5 bullet points
                - If no memory is relevant, just say "No relevant context."
                
"""

                synthesis_response = await asyncio.to_thread(self.fast_llm.generate_text, synthesis_prompt)
                logs['step4_synthesis'] = {
                    "content": synthesis_response,
                    "model": self.fast_llm.provider_name,
                    "prompt": synthesis_prompt
                }
                response_input = synthesis_response
            else:
                # Optimized Remote Path
                print("DEBUG: Optimizing - Reasoning directly in final response...")
                response_input = None
                
                # Directly append vector results to the response prompt context
                semantic_context = "\n".join([f"- {item['content']}" for item in vector_results])
                
                response_prompt = f"""
                You are a helpful AI assistant with long-term memory.
                
                User Message: "{user_message}"
                
                Your Memory of This User:
                {context_str}
                
                Relevant Semantic Context (Past Conversations):
                {semantic_context if vector_results else "No relevant past conversations found."}
                
                Instructions:
                - Respond naturally and helpfully to the user's message
                - Use your memory to personalize your response (e.g. if they prefer Rust, give code in Rust)
                - If the user is updating a fact, acknowledge the update
                - NEVER mention "memory", "context", "graph database", or internal systems to the user
                - Respond as if you naturally remember these things about them
                """
                
                final_response = await asyncio.to_thread(self.remote_llm.generate_text, response_prompt)
                synthesis_response = "Direct response path (no separate synthesis)."
                logs['step4_synthesis'] = {
                    "content": synthesis_response,
                    "model": self.remote_llm.provider_name,
                    "prompt": "Direct Response Prompt"
                }
                logs['step5_response'] = {
                    "prompt": response_prompt,
                    "model": self.remote_llm.provider_name
                }


            if response_input:
                response_prompt = f"""
                You are a helpful AI assistant with long-term memory. You remember things about the user from previous conversations.
                
                User Message: "{user_message}"
                
                What you remember about this user:
                {response_input}
                
                Instructions:
                - Respond directly and helpfully to the user's message
                - Use what you remember to personalize your response (e.g. if they prefer Rust, write code in Rust without being asked)
                - Do NOT explain your reasoning or analysis process
                - Do NOT mention "memory", "context", "database" or internal systems
                - Respond as if you naturally remember these things
                - Be concise and directly address what the user asked for
                """
                
                logs['step5_response'] = {
                    "prompt": response_prompt,
                    "model": self.remote_llm.provider_name
                }
                
                # Check if search is needed
                tools_config = None
                if planner_response.get('needs_search'):
                    print("DEBUG: Search tool requested by planner.")
                    tools_config = {'google_search': {}}
                
                    # If searching, we want the grounding metadata
                    gen_result = await asyncio.to_thread(
                        self.remote_llm.generate_text, 
                        response_prompt, 
                        tools=tools_config,
                        return_full_response=True
                    )
                    
                    if isinstance(gen_result, dict):
                        final_response = gen_result['text']
                        grounding_metadata = gen_result.get('grounding_metadata')
                    else:
                        final_response = gen_result # Should be string if fallback
                        grounding_metadata = None
                else:
                    grounding_metadata = None
                    final_response = await asyncio.to_thread(
                        self.remote_llm.generate_text, 
                        response_prompt
                    )
            
            return ChatResponse(
                response=final_response,
                context_used=synthesis_response,
                step_logs=logs,
                grounding_metadata=grounding_metadata
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

    async def run_async_update(self, user_message: str, assistant_response: str, user_id: str, retrieved_context: dict = None):
        """Step 6 implementation: Embed turn and update Neo4j using Local LLM."""
        print("Running async update...")

        # Prevent memory pollution from error messages
        error_signatures = [
            "Thinking process interrupted",
            "I'm currently experiencing system issues.",
            "Error during processing.",
            "System limited"
        ]
        if any(err in assistant_response for err in error_signatures):
            print("Skipping async update due to error response.")
            return
        
        llm_to_use = self.context_llm

        # --- Sub-step 6a: Semantic Filter (Vector DB Hygiene) ---
        semantic_filter_prompt = f"""
        You are a Memory Filter in a long-term memory system for an AI assistant.
        Your job is to decide if this conversation turn contains USER-SPECIFIC information worth remembering across future conversations.
        
        User: "{user_message}"
        Assistant: "{assistant_response}"
        
        SAVE ONLY user-specific information such as:
        - Personal preferences ("I prefer Rust", "I'm vegetarian")
        - Facts about the user ("My name is Adi", "I work at Google", "My best friend is Tobey")
        - Constraints they set ("Never use emojis", "Keep responses short")
        - Long-term instructions ("Always explain with analogies")
        - Important personal context ("I'm preparing for an interview next week")
        
        DO NOT SAVE:
        - General knowledge the AI generated (code examples, explanations, tutorials)
        - The content of what the assistant produced (a web server program, a poem, etc.)
        - Information that any AI would already know (how Rust works, what actix-web is)
        - Simple task completions ("User asked for X, assistant provided X")
        
        Output JSON:
        - meaningful_content: (boolean) true ONLY if there is user-specific info to remember
        - summary: (string) a short summary of the USER-SPECIFIC info only, or null
        - reasoning: (string) why this is or isn't user-specific
        
        Examples:
        User: "I prefer Rust" → SAVE: "User prefers Rust for coding examples"
        User: "Write me a web server" → SKIP (general task, nothing personal to remember)
        User: "My meeting is at 3pm tomorrow" → SAVE: "User has a meeting at 3pm tomorrow"
        User: "Explain how TCP works" → SKIP (general knowledge request)
        """
        try:
            semantic_analysis = await asyncio.to_thread(llm_to_use.generate_json, semantic_filter_prompt)
            print(f"DEBUG: Semantic Analysis: {json.dumps(semantic_analysis, indent=2)}")
            
            if semantic_analysis.get('meaningful_content') and semantic_analysis.get('summary'):
                # Save ONLY the clean summary - no original turn needed
                summary = semantic_analysis['summary']
                
                should_save = True
                
                # Check against retrieved context to avoid duplication
                if retrieved_context and retrieved_context.get('vector'):
                    for item in retrieved_context['vector']:
                        # Check for exact or near match in what we JUST retrieved
                        # This saves a DB call if we already know this info
                        if summary.strip() == item['content'].strip():
                             print(f"⊘ Skipped Vector DB (Already in retrieved context: '{summary[:50]}...')")
                             should_save = False
                             break
                
                if should_save:
                    # Deduplication check: search for similar content before saving (Double check)
                    import time
                    existing_results = self.memory_manager.search_vector_memory(summary, n_results=1)
                
                # Check if we already have very similar content
                should_save = True
                if existing_results and existing_results.get('documents') and existing_results['documents'][0]:
                    existing_doc = existing_results['documents'][0][0]
                    
                    # Method 1: Exact text match
                    if existing_doc.strip() == summary.strip():
                        print(f"⊘ Skipped Vector DB (Exact duplicate: '{summary[:50]}...')")
                        should_save = False
                    # Method 2: Distance-based similarity (ChromaDB uses L2 by default)
                    elif existing_results.get('distances') and existing_results['distances'][0]:
                        top_distance = existing_results['distances'][0][0]
                        print(f"DEBUG: ChromaDB distance for '{summary[:40]}...': {top_distance} (existing: '{existing_doc[:40]}...')")
                        if top_distance < 0.5:  # L2 distance threshold
                            print(f"⊘ Skipped Vector DB (Similar content, distance: {top_distance:.4f})")
                            should_save = False
                
                if should_save:
                    turn_id = f"turn_{user_id}_{int(time.time()*1000)}"
                    self.memory_manager.add_vector_memory(
                        turn_id, 
                        summary,  # Save ONLY the summary
                        metadata={
                            "user_id": user_id, 
                            "timestamp": time.time(), 
                            "type": "semantic_memory"
                        }
                    )
                    print(f"✓ Saved to Vector DB: '{summary[:50]}...'")
            else:
                print("⊘ Skipped Vector DB (No long-term value)")
        except Exception as e:
            print(f"Semantic filter failed: {e}. Skipping save to avoid pollution.")
            # Changed: Do NOT save on failure to avoid polluting the DB

        # --- Sub-step 6b: Enhanced Graph Extraction with Strength Filter ---
        extraction_prompt = f"""
        Extract structured memory nodes from this conversation for a Neo4j graph.
        User: "{user_message}"
        Assistant: "{assistant_response}"
        User: "{user_message}"
        Assistant: "{assistant_response}"
        User ID: "{user_id}"

        EXISTING KNOWLEDGE (Do NOT re-extract these unless updating/correcting):
        {retrieved_context['graph'] if retrieved_context and retrieved_context.get('graph') else "No existing graph context retrieved."}
        
        Allowed Node Labels: 'Preference', 'Fact', 'Entity', 'Constraint', 'Commitment', 'Instruction'.
        
        CRITICAL EXTRACTION RULES:
        1. ONLY extract information that is EXPLICITLY stated by the user or assistant or is a fact/indentifiable preference of the user.
        2. NEVER assume a user preference based on an assistant's choice of framework/tool in an example (e.g., if assistant uses 'actix-web', do NOT save it as a user preference unless the user specifically said "I like actix-web" or "Always use actix-web").
        3. IGNORE: simple examples, trivial requests ("give me hello world"), greetings, small talk.
        4. Each extraction must have a significance_score (1-10) based on long-term value.
        5. ONLY include nodes with significance_score >= 6.
        
        SPECIFIC NODE RULES:
        - Preference/Constraint/Instruction: ONLY save if the user EXPLICITLY requested it (e.g. "I prefer X", "Never do Y", "Always do Z").
        - Fact: Save objective information about the user mentioned in the turn.
        - Entity: Save people, places, or significant things mentioned.
        - Commitment: Save promises the ASSISTANT made to the user for the future.
        
        EXACT SCHEMAS FOR EACH NODE TYPE:
        
        Preference: {{ "id": "pref_xxx", "name": "preference_name", "value": "preference_value", "status": "active" }}
        Fact: {{ "id": "fact_xxx", "statement": "complete factual statement", "status": "active" }}
        Entity: {{ "id": "entity_xxx", "name": "entity_name", "type": "Person|Place|Thing|Concept", "status": "active", "context": "optional context" }}
        Constraint: {{ "id": "const_xxx", "name": "constraint_name", "description": "detailed rule", "status": "active" }}
        Commitment: {{ "id": "commit_xxx", "description": "what was promised", "due_date": "when|null", "status": "active" }}
        Instruction: {{ "id": "instr_xxx", "description": "behavior instruction", "priority": "high|normal|low", "status": "active" }}
        
        Instructions:
        1. Identify any new or updated information with lasting importance based ONLY on explicit statements.
        2. If a PREVIOUS fact is now false, use operation="DELETE" or status="obsolete".
        3. DO NOT extrapolate or guess user preferences.
        
        Output JSON:
        {{
            "significance_score": 1-10,
            "should_save": boolean,
            "nodes": [
                {{
                    "label": "Preference|Fact|Entity|Constraint|Commitment|Instruction",
                    "id": "unique_id_string", 
                    "properties": {{ ...use exact schema from above... }},
                    "operation": "MERGE|DELETE|UPDATE" 
                }}
            ],
            "relationships": [
                {{ "source_label": "...", "source_id": "...", "type": "...", "target_label": "...", "target_id": "..." }}
            ]
        }}
        """
        
        try:
            updates = await asyncio.to_thread(llm_to_use.generate_json, extraction_prompt)
            print(f"DEBUG: Async Update JSON: {json.dumps(updates, indent=2)}")
            
            # Check significance score before saving
            significance = updates.get('significance_score', 0)
            should_save = updates.get('should_save', False)
            
            if significance < 6 or not should_save:
                print(f"⊘ Skipped Graph Update (Low significance: {significance}/10)")
                return
            
            print(f"✓ Graph Update Approved (Significance: {significance}/10)")
            
            if updates.get('nodes'):
                for node in updates['nodes']:
                    label = node['label']
                    props = node.get('properties', {}).copy()
                    op = node.get('operation', 'MERGE').upper()
                    
                    if 'id' in node:
                        props['id'] = node['id']
                    
                    # Handle Deletions/Updates
                    if op == 'DELETE' or props.get('status') == 'obsolete':
                         # If we have an ID, mark it as obsolete directly
                         if 'id' in props:
                            # We can use supersede to self (hack) or just run a query
                            # For now, let's use a custom query to "delete"/archive
                            archive_query = f"MATCH (n:{label} {{id: $id}}) SET n.status = 'obsolete', n.archived_at = timestamp() RETURN n"
                            self.memory_manager.run_graph_query(archive_query, {"id": props['id']})
                            print(f"DEBUG: Archived node {props['id']}")
                         continue

                    # --- Memory Gardener: Dedup ALL node types ---
                    existing = []
                    
                    if label == 'Fact':
                        # Check by statement text
                        stmt = props.get('statement', '')
                        if stmt:
                            check_query = f"""
                            MATCH (u:User {{id: $uid}})-[:HAS_FACT]->(n:Fact {{status: 'active'}})
                            WHERE n.statement = $stmt
                            RETURN n.id as id
                            """
                            existing = self.memory_manager.run_graph_query(check_query, {"uid": user_id, "stmt": stmt})
                            if existing:
                                print(f"⊘ Skipped duplicate Fact: '{stmt[:50]}'")
                                continue
                    
                    elif label == 'Entity':
                        # Check by name
                        name = props.get('name', '')
                        if name:
                            check_query = f"""
                            MATCH (u:User {{id: $uid}})-[:HAS_ENTITY]->(n:Entity {{name: $name, status: 'active'}})
                            RETURN n.id as id
                            """
                            existing = self.memory_manager.run_graph_query(check_query, {"uid": user_id, "name": name})
                            if existing:
                                # Update existing entity instead of creating duplicate
                                old_id = existing[0]['id']
                                print(f"⊘ Entity '{name}' already exists (id: {old_id}), updating props")
                                update_query = f"MATCH (n:Entity {{id: $id}}) SET n += $props RETURN n"
                                self.memory_manager.run_graph_query(update_query, {"id": old_id, "props": props})
                                continue
                    
                    elif label in ['Preference', 'Constraint', 'Instruction', 'Commitment'] and 'name' in props:
                        # Check by name for named node types
                        check_query = f"""
                        MATCH (u:User {{id: $uid}})-[:HAS_{label.upper()}]->(n:{label} {{name: $name, status: 'active'}})
                        RETURN n.id as id
                        """
                        existing = self.memory_manager.run_graph_query(check_query, {"uid": user_id, "name": props['name']})
                    
                    # Add new node
                    self.memory_manager.add_graph_node(label, props)
                    
                    # Connect to User node
                    self.memory_manager.create_relationship(
                        'User', user_id,
                        f'HAS_{label.upper()}',
                        label, props['id']
                    )
                    
                    # Apply SUPERSEDES if older version found (for Preference/Constraint/etc)
                    if existing:
                        old_id = existing[0]['id']
                        if old_id != props.get('id'):
                            self.memory_manager.supersede_node(old_id, props.get('id'), label)
            
            if updates.get('relationships'):
                for rel in updates['relationships']:
                    self.memory_manager.create_relationship(
                        rel['source_label'], rel['source_id'],
                        rel['type'],
                        rel['target_label'], rel['target_id'],
                        rel.get('properties', {})
                    )
            print("Memory Gardener: Graph updated and de-conflicted.")
        except Exception as e:
            print(f"Async update failed: {e}")
            import traceback
            traceback.print_exc()

    @property
    def context_llm(self) -> LLMProvider:
        return LLMFactory.get_provider("groq")
