import streamlit as st
import httpx
import json

# -------------------------------
# Configuration
# -------------------------------
PROXY_URL = "http://localhost:8000/api/jira/issue"

# -------------------------------
# Helper Functions
# -------------------------------
def fetch_jira_details(issue_key: str):
    """
    Calls the Jira proxy API and returns structured response.
    Works even if API returns 404 or 500.
    """
    try:
        r = httpx.post(
            PROXY_URL,
            json={"issue_key": issue_key},
            timeout=60.0
        )

        try:
            data = r.json()
        except Exception:
            data = {"detail": r.text}

        return {
            "status_code": r.status_code,
            "data": data
        }

    except httpx.RequestError as e:
        return {
            "status_code": "connection_error",
            "data": {"detail": str(e)}
        }


def render_generic_json(data, prefix=""):
    """
    Recursively renders a dictionary in readable format.
    """
    if not isinstance(data, dict):
        st.write(f"{prefix}{data}")
        return

    for k, v in data.items():
        label = k.replace("_", " ").title()

        if isinstance(v, dict):
            st.write(f"{prefix}**{label}:**")
            render_generic_json(v, prefix + "  ")
        else:
            st.write(f"{prefix}**{label}:** {v}")


# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(
    page_title="Jira MCP Assistant",
    page_icon="🎫"
)

st.title("🎫 Jira MCP Assistant")

# -------------------------------
# Chat State
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# Render Chat History
# -------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):

        content = msg["content"]

        if isinstance(content, dict) and "status_code" in content:
            status = content["status_code"]
            data = content["data"]

            if status == 200:
                st.success(f"✅ Success (HTTP {status})")
            elif status == 404:
                st.warning(f"⚠️ Issue not found (HTTP {status})")
            elif status == "connection_error":
                st.error("❌ Unable to connect to backend service")
            else:
                st.error(f"❌ API returned HTTP {status}")

            render_generic_json(data)

        else:
            st.markdown(content)

# -------------------------------
# Chat Input
# -------------------------------
if prompt := st.chat_input("Enter Jira Issue ID (e.g., KAN-30)"):

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):

        with st.spinner("Fetching Jira issue..."):

            result = fetch_jira_details(prompt)

            status = result["status_code"]
            data = result["data"]

            # Show status banner
            if status == 200:
                st.success(f"✅ Success (HTTP {status})")

            elif status == 404:
                st.warning(f"⚠️ Issue not found (HTTP {status})")

            elif status == "connection_error":
                st.error("❌ Could not connect to backend")

            else:
                st.error(f"❌ API returned HTTP {status}")

            # Render response
            render_generic_json(data)

            # Store assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": result
            })