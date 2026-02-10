import streamlit as st
import requests
import uuid

# Configuration
API_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Hybrid Memory RAG", page_icon="🧠")

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

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("details"):
            with st.expander("Memory Context & Reasoning"):
                st.json(message["details"])

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
                    API_URL, 
                    json={"message": prompt, "user_id": st.session_state.user_id}
                )
                if response.status_code == 200:
                    data = response.json()
                    bot_reply = data["response"]
                    details = data.get("step_logs")
                    
                    st.markdown(bot_reply)
                    if details:
                        with st.expander("Memory Context & Reasoning"):
                            st.json(details)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": bot_reply,
                        "details": details
                    })
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")
