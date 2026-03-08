# import streamlit as st
# import httpx
# import uuid

# BOT_URL = "http://localhost:9000/api/messages"

# st.title("MCP Bot Test UI")

# if "conv_id" not in st.session_state:
#     st.session_state.conv_id = str(uuid.uuid4())

# user_input = st.text_input("Enter Jira Ticket ID (e.g., KAN-30)")

# if st.button("Send") and user_input:
#     payload = {
#         "type": "message",
#         "text": user_input,
#         "conversation": {"id": st.session_state.conv_id},
#         "from": {"id": "user"},
#     }

#     try:
#         with st.spinner("Talking to MCP Proxy..."):
#             r = httpx.post(BOT_URL, json=payload, timeout=65.0)
#             if r.status_code == 200:
#                 answer = r.json().get("reply", "No response")
#                 st.success(f"**Bot:** {answer}")
#             else:
#                 st.error(f"Error: {r.status_code} - {r.text}")
#     except Exception as e:
#         st.error(f"Connection failed: {e}")

# import streamlit as st
# import httpx

# # Point this to your Kong Gateway (jira-proxy-route)
# PROXY_URL = "http://localhost:8000/jira-proxy/jira_lookup"

# st.set_page_config(page_title="Jira MCP Assistant", page_icon="🎫")
# st.title("🎫 Jira MCP Assistant")

# # Initialize chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Display chat history
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # Chat Input
# if prompt := st.chat_input("Enter Jira Ticket ID (e.g., KAN-30)"):
#     # Add user message to history
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Call Proxy
#     with st.chat_message("assistant"):
#         with st.spinner("Fetching details from Jira..."):
#             try:
#                 # Match proxy.py's expected payload {"ticket": "..."}
#                 r = httpx.post(PROXY_URL, json={"ticket": prompt}, timeout=60.0)
#                 if r.status_code == 200:
#                     reply = r.json().get("result", "No details found.")
#                 else:
#                     reply = f"❌ Error: {r.status_code}\n\n{r.text}"
#             except Exception as e:
#                 reply = f"⚠️ Connection failed: {str(e)}"
            
#             st.markdown(reply)
#             st.session_state.messages.append({"role": "assistant", "content": reply})

import streamlit as st
import httpx
import json

PROXY_URL = "http://localhost:8000/jira-proxy/jira_lookup"

def fetch_jira_details(ticket_id: str):
    """Handles the API call and ensures the result is a dictionary."""
    try:
        r = httpx.post(PROXY_URL, json={"ticket": ticket_id}, timeout=60.0)
        r.raise_for_status()
        res = r.json().get("result", {})

        # If the result is a string, parse it into a dict
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except json.JSONDecodeError:
                pass 
        return res
    except Exception as e:
        return {"Error": str(e)}

def render_generic_json(data):
    """Renders dict as bold lines; handles non-dict fallbacks."""
    if not isinstance(data, dict):
        st.write(data)
        return str(data)

    output_lines = []
    for k, v in data.items():
        label = k.replace("_", " ").title()
        line = f"**{label}:** {v}"
        st.write(line) # Use st.write for cleaner vertical spacing
        output_lines.append(line)
    return "\n\n".join(output_lines)

# --- UI Layout ---
st.set_page_config(page_title="Jira MCP Assistant", page_icon="🎫")
st.title("🎫 Jira MCP Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Main Input Logic
if prompt := st.chat_input("Enter Jira Ticket ID"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Fetching..."):
            result = fetch_jira_details(prompt)
            reply_text = render_generic_json(result)
            st.session_state.messages.append({"role": "assistant", "content": reply_text})

