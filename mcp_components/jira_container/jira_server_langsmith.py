import os
from dotenv import load_dotenv
# Load env vars before other libs are loaded (langsmith)
load_dotenv()

import re, json
import base64
import httpx
from fastmcp import FastMCP

from contextlib import asynccontextmanager
from langsmith import Client
from langchain_core.tracers.context import tracing_v2_enabled
from shared.tracing_utils import secure_trace, secure_mcp_tool

# --- 1. STANDARDIZED CONFIG (Validate at startup) ---
JIRA_URL = os.getenv("JIRA_URL", "").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "").strip()
JIRA_TOKEN = os.getenv("JIRA_API_KEY", "").strip()
PROJECT_NAME = os.getenv("LANGCHAIN_PROJECT", "mcp-jira-gateway")

if not all([JIRA_URL, JIRA_EMAIL, JIRA_TOKEN]):
    raise RuntimeError("❌ Missing required JIRA environment variables!")

ls_client = Client() 
jira_client = None

@asynccontextmanager
async def lifespan(mcp: FastMCP):
    global jira_client
    # Limits prevent 'socket exhaustion' in high-traffic production
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    async with httpx.AsyncClient(timeout=10.0, limits=limits) as client:
        jira_client = client
        yield

mcp = FastMCP("jira-client", lifespan=lifespan)

@secure_trace(name="Jira API Network Call")
async def fetch_from_jira(endpoint: str, headers: dict, langsmith_extra: dict = None):
    return await jira_client.get(endpoint, headers=headers)

@mcp.tool()
@secure_mcp_tool(name="Get Jira Issue", service="jira-gateway")
async def get_issue_details(issue_key: str) -> str:
    with tracing_v2_enabled(project_name=PROJECT_NAME, client=ls_client):
        issue_key = issue_key.strip().upper()
        if not re.match(r"^[A-Z0-9]+-\d+$", issue_key):
            return f"Error: '{issue_key}' is invalid."

        auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_auth}", "Accept": "application/json"}

        try:
            endpoint = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
            response = await fetch_from_jira(endpoint, headers)

            # --- 2. STANDARDIZED ERROR TAGGING ---
            if response.status_code == 200:
                
                fields = response.json().get('fields', {})
                summary = fields.get('summary', 'No summary provided')
                status = fields.get('status', {}).get('name', 'Unknown status')
                description = fields.get('description') or "No description provided."

                format_data = {
                    "issue_key": issue_key,
                    "summary": summary,
                    "status": status,
                    "description": description
                }

                return json.dumps(format_data)
            
            # Explicitly tell LangSmith this was an API failure
            error_msg = f"❌ Jira API Error: {response.status_code}"
            return error_msg
            
        except Exception as e:
            return f"❌ System Error: {str(e)}"

app = mcp.http_app(path="/mcp") 

if __name__ == "__main__":
    mcp.run()
