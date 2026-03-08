import streamlit as st
import httpx

# -------------------------------
# Configuration
# -------------------------------
PROXY_URL = "http://localhost:8000/api/jira/issue"
COMMENT_API = "http://localhost:8000/api/jira/comment"

# -------------------------------
# Helper Functions
# -------------------------------
def fetch_jira_details(issue_key: str):

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


def add_comment(issue_key: str, comment: str):

    try:
        r = httpx.post(
            COMMENT_API,
            json={
                "issue_key": issue_key,
                "comment": comment
            },
            timeout=60.0
        )

        try:
            data = r.json()
        except:
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
# Chat Input (Issue Lookup)
# -------------------------------
if prompt := st.chat_input("Enter Jira Issue ID (e.g., KAN-30)"):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Fetching Jira issue..."):

            result = fetch_jira_details(prompt)

            status = result["status_code"]
            data = result["data"]

            if status == 200:
                st.success(f"✅ Success (HTTP {status})")

            elif status == 404:
                st.warning(f"⚠️ Issue not found (HTTP {status})")

            elif status == "connection_error":
                st.error("❌ Could not connect to backend")

            else:
                st.error(f"❌ API returned HTTP {status}")

            render_generic_json(data)

            st.session_state.messages.append({
                "role": "assistant",
                "content": result
            })


# -------------------------------
# Add Comment Section
# -------------------------------
st.divider()
st.subheader("💬 Add Comment to Jira Issue")

issue_key = st.text_input(
    "Issue Key",
    placeholder="KAN-30"
)

comment_text = st.text_area(
    "Comment",
    placeholder="Write your comment here..."
)

if st.button("Add Comment"):

    if not issue_key or not comment_text:

        st.warning("Please provide both Issue Key and Comment")

    else:

        with st.spinner("Posting comment..."):

            result = add_comment(issue_key, comment_text)

            status = result["status_code"]
            data = result["data"]

            if status in [200, 201]:

                comment_result = data.get("comment_result", {})

                st.success("✅ Comment added successfully")

                st.write("**Issue:**", issue_key)
                st.write("**Comment ID:**", comment_result.get("id"))

                with st.expander("Full Jira Response"):
                    st.json(data)

            elif status == 404:

                st.warning("⚠️ Issue not found")

                with st.expander("Error Details"):
                    st.json(data)

            elif status == "connection_error":

                st.error("❌ Could not connect to backend")

            else:

                st.error(f"❌ API returned HTTP {status}")

                with st.expander("Full Error Response"):
                    st.json(data)