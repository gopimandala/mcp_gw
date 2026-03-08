import streamlit as st
import httpx
import json

# -------------------------------
# Configuration
# -------------------------------
PROXY_URL = "http://localhost:8021/api/jira/issue"

# -------------------------------
# Helper Functions
# -------------------------------
def fetch_jira_details(issue_key: str):
    """
    Calls the Jira proxy API and returns a dict.
    """
    try:
        r = httpx.post(PROXY_URL, json={"issue_key": issue_key}, timeout=60.0)
        r.raise_for_status()
        res = r.json()  # return full JSON directly
        return res
    except Exception as e:
        return {"Error": str(e)}


def render_generic_json(data, prefix=""):
    """
    Recursively renders a dictionary as bold lines in Streamlit.
    Nested dictionaries are indented.
    """
    if not isinstance(data, dict):
        st.write(f"{prefix}{data}")
        return str(data)

    output_lines = []

    for k, v in data.items():
        label = k.replace("_", " ").title()
        if isinstance(v, dict):
            st.write(f"**{prefix}{label}:**")  # just the label
            output_lines.append(f"{prefix}{label}:")
            output_lines.append(render_generic_json(v, prefix=prefix + "  "))  # indent nested
        else:
            line = f"**{prefix}{label}:** {v}"
            st.write(line)
            output_lines.append(line)

    return "\n".join(output_lines)


# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Jira MCP Assistant", page_icon="🎫")
st.title("🎫 Jira MCP Assistant")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display old messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        content = msg["content"]
        # If content is a dict, render recursively
        if isinstance(content, dict):
            render_generic_json(content)
        else:
            st.markdown(content)

# Chat input
if prompt := st.chat_input("Enter Jira Issue ID (e.g., KAN-30)"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Jira proxy and render assistant response
    with st.chat_message("assistant"):
        with st.spinner("Fetching..."):
            result = fetch_jira_details(prompt)
            render_generic_json(result)  # display nicely in chat
            # Store raw dict in session state to preserve structure
            st.session_state.messages.append({"role": "assistant", "content": result})