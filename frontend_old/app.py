import streamlit as st
import requests
import uuid

# Configuration
API_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Hybrid Memory RAG", page_icon="🧠", layout="wide")

st.title("🧠 Hybrid Memory RAG")
st.caption("powered by Gemini 1.5 Flash, ChromaDB & Neo4j")

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id_input" not in st.session_state:
    st.session_state.user_id_input = "Adi" # Default for stable memory

with st.sidebar:
    st.header("Memory Settings")
    st.session_state.user_id_input = st.text_input("Memory User ID", value=st.session_state.user_id_input)
    st.caption(f"Current internal ID: {st.session_state.user_id_input}")
    if st.button("Clear Frontend Chat"):
        st.session_state.messages = []
        st.rerun()

st.session_state.user_id = st.session_state.user_id_input

def render_log_details(logs):
    if not logs:
        return

    # Tabs for different pipeline stages to keep it clean
    tab_titles = ["🕒 Temporal", "🧠 Planner", "🔍 Retrieval", "⚖️ Reconcile", "✍️ Synthesis", "🤖 Final Prompt"]
    tabs = st.tabs(tab_titles)

    # 1. Temporal Check
    with tabs[0]:
        s0 = logs.get("step0_temporal_check", {})
        if s0:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Override Detected", "Yes" if s0.get("is_override") else "No")
            with c2:
                model_name = s0.get("model", "Unknown")
                st.caption(f"**Model:** {model_name}")
                if s0.get("conflict_summary"):
                    st.warning(f"Conflict: {s0.get('conflict_summary')}")
                elif s0.get("target_node_label"):
                    st.info(f"Targeting: {s0.get('target_node_label')}")
                else:
                    st.success("No temporal conflicts found.")
            
            if s0.get("prompt"):
                with st.expander("View Prompt", expanded=False):
                    st.code(s0["prompt"], language="text")
        else:
            st.write("No temporal check data.")

    # 2. Planner
    with tabs[1]:
        s1 = logs.get("step1_planner", {})
        if s1:
            st.caption(f"**Model:** {s1.get('model', 'Unknown')}")
            
            if s1.get("search_terms"):
                st.markdown("**Vector Search Terms:**")
                # st.write(s1["search_terms"])
                for term in s1["search_terms"]:
                    st.code(term, language="text")
            
            if s1.get("cypher_query"):
                st.markdown("**Graph Query:**")
                st.code(s1["cypher_query"], language="cypher")

            if s1.get("prompt"):
                with st.expander("View Prompt", expanded=False):
                    st.code(s1["prompt"], language="text")
        else:
            st.write("No planner data.")

    # 3. Retrieval
    with tabs[2]:
        s2 = logs.get("step2_retrieval", {})
        if s2:
            if s2.get("search_terms"):
                st.markdown("**🔍 Vector Search Terms:**")
                st.info(", ".join(s2.get("search_terms")))
            
            st.markdown("**Vector Source:** `ChromaDB (all-MiniLM-L6)`")
            vectors = s2.get("vector", [])
            if vectors:
                for i, v in enumerate(vectors):
                    with st.expander(f"Chunk {i+1}", expanded=False):
                        if isinstance(v, dict):
                            st.caption(f"ID: {v.get('id', 'N/A')}")
                            st.text(v.get('content', str(v)))
                        else:
                            st.text(v)
            else:
                st.info("No relevant vector memories found.")

            st.divider()
            
            if s2.get("cypher_query"):
                st.markdown("**🕸️ Graph Query:**")
                st.code(s2.get("cypher_query"), language="cypher")

            st.markdown("**Graph Source:** `Neo4j`")
            graph = s2.get("graph", [])
            if graph:
                st.write(graph)
            else:
                st.info("No relevant graph nodes found.")
        else:
            st.write("No retrieval data available.")

    # 4. Reconciliation
    with tabs[3]:
        s3 = logs.get("step3_reconciliation", {})
        if s3:
            if isinstance(s3, dict):
                st.caption(f"**Method:** {s3.get('model', 'Rule Based')}")
                content = s3.get("content", "")
            else:
                st.caption("**Method:** Legacy/Unknown")
                content = str(s3)
            
            st.text_area("Context Snapshot", content, height=300)
        else:
            st.write("No reconciliation data.")

    # 5. Synthesis
    with tabs[4]:
        s4 = logs.get("step4_synthesis", {})
        if s4:
            if isinstance(s4, dict):
                st.caption(f"**Model:** {s4.get('model', 'Unknown')}")
                st.markdown(s4.get("content", ""))
                if s4.get("prompt"):
                    with st.expander("View Prompt", expanded=False):
                        st.code(s4["prompt"], language="text")
            else:
                st.markdown(str(s4))
        else:
            st.write("No synthesis data.")

    # 6. Final Prompt
    with tabs[5]:
        s5 = logs.get("step5_response", {})
        if s5:
            st.caption(f"**Model:** {s5.get('model', 'Unknown')}")
            st.markdown("**Final Prompt sent to Model:**")
            st.code(s5.get("prompt", "No prompt found"), language="text")
        else:
            st.write("No final prompt data.")



def render_grounding(metadata):
    if not metadata or "chunks" not in metadata:
        return
    
    chunks = metadata["chunks"]
    if not chunks:
        return
        
    with st.expander("🌍 Google Search Sources", expanded=False):
        for i, chunk in enumerate(chunks, 1):
            title = chunk.get("title", "Untitled")
            url = chunk.get("url", "#")
            st.markdown(f"{i}. [{title}]({url})")

# Display Chat History
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(message["content"])
            
            # Show grounding sources if available
            if message.get("grounding_metadata"):
                render_grounding(message["grounding_metadata"])
            
            if message.get("details"):
                with st.expander("Memory Context & Reasoning"):
                    render_log_details(message["details"])

# Chat Input
if prompt := st.chat_input("What would you like to say?"):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}", 
                    json={"message": prompt, "user_id": st.session_state.user_id}
                )
                if response.status_code == 200:
                    data = response.json()
                    bot_reply = data["response"]
                    details = data.get("step_logs")
                    grounding = data.get("grounding_metadata")
                    
                    st.markdown(bot_reply)
                    
                    if grounding:
                        render_grounding(grounding)
                        
                    if details:
                        with st.expander("Memory Context & Reasoning"):
                            render_log_details(details)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": bot_reply,
                        "details": details,
                        "grounding_metadata": grounding
                    })
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")

