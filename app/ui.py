import streamlit as st
import requests
import os

st.set_page_config(page_title="Cinema Scout", layout="centered")

st.title("Cinema Scout")
st.caption("Autonomous Indie Film Agent")

AGENT_API_URL = os.getenv("AGENT_API_URL", "http://agent-api:8000/chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

def clear_chat():
    st.session_state.messages = []


with st.sidebar:
    st.button("Clear Chat", on_click=clear_chat)
    st.markdown("System Status: Online")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about a movie or request a download..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("Analyzing request...")

        try:
            response = requests.post(
                AGENT_API_URL,
                json={"input": prompt},
                timeout=120
            )
            response.raise_for_status()

            data = response.json()
            clean_text = data.get("output", "No response generated.")

            response_placeholder.markdown(clean_text)
            st.session_state.messages.append({"role": "assistant", "content": clean_text})

        except requests.exceptions.RequestException as e:
            error_msg = f"Network Error: Could not reach the Agent API. Details: {str(e)}"
            response_placeholder.error(error_msg)
        except Exception as e:
            error_msg = f"System Error: {str(e)}"
            response_placeholder.error(error_msg)