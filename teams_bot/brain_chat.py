# ui_brain.py
import streamlit as st
import requests
import json

# Brain server config
BRAIN_URL = "http://localhost:9000/run_brain"

st.set_page_config(page_title="Brain UI", page_icon="🧠")

st.title("Brain UI – Jira Assistant")

# Input for user request
user_request = st.text_area(
    "Enter your request for the Brain:",
    value="Check KAN-30 and comment that it will be done in the next 2 hours",
    height=100
)

if st.button("Submit"):
    if not user_request.strip():
        st.warning("Please enter a request.")
    else:
        try:
            resp = requests.post(BRAIN_URL, json={"user_request": user_request})
            if resp.status_code == 200:
                data = resp.json()
                st.success("Execution successful!")

                execution_results = data.get("execution_results", [])
                
                for i, result in enumerate(execution_results):
                    output = result.get("output", {})
                    
                    if isinstance(output, dict):
                        # Display each key-value pair on a separate line
                        for key, value in output.items():
                            if isinstance(value, dict):
                                # Nested dict - flatten it
                                st.write(f"**{key}:**")
                                for nested_key, nested_value in value.items():
                                    st.write(f"  {nested_key}: {nested_value}")
                            else:
                                st.write(f"**{key}:** {value}")
                    else:
                        # Not a dict - show as single chunk of text
                        st.write(output)

            else:
                st.error(f"Brain server returned {resp.status_code}: {resp.text}")

        except Exception as e:
            st.error(f"Failed to call Brain server: {e}")