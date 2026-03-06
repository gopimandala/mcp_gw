#!/usr/bin/env python3
import os
import re
import base64
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# 2. Create MCP server
mcp = FastMCP("jira-client")

@mcp.tool()
async def get_issue_details(issue_key: str) -> str:
    """
    Get detailed information about a specific Jira issue (e.g., 'KAN-65').
    """
    # Sanitize and validate the issue key
    issue_key = issue_key.strip().upper()
    if not re.match(r"^[A-Z0-9]+-\d+$", issue_key):
        return f"Error: '{issue_key}' is not a valid Jira issue key format."

    # Retrieve and clean environment variables
    url = os.getenv("JIRA_URL", "").rstrip('/')
    email = os.getenv("JIRA_EMAIL", "").strip()
    token = os.getenv("JIRA_API_KEY", "").strip()

    print(f"URL: {url}")
    print(f"Email: {email}")
    print(f"Token: {token[:10]}...")

    if not all([url, email, token]):
        return "Error: JIRA_URL, JIRA_EMAIL, or JIRA_API_KEY is not set in .env"

    # Prepare Basic Auth header (Email:API_Token encoded in Base64)
    auth_str = f"{email}:{token}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            # SWITCHED TO API v2: This returns description as a readable string
            # instead of the complex ADF JSON tree.
            endpoint = f"{url}/rest/api/2/issue/{issue_key}"
            response = await client.get(endpoint, headers=headers, timeout=10.0)

            if response.status_code == 200:
                data = response.json()
                fields = data.get('fields', {})
                
                summary = fields.get('summary', 'No summary provided')
                status = fields.get('status', {}).get('name', 'Unknown status')
                
                # In v2, this is a plain string or null
                description = fields.get('description') or "No description provided."

                return (
                    f"✅ SUCCESS: {issue_key}\n"
                    f"Summary: {summary}\n"
                    f"Status: {status}\n"
                    f"Description:\n{description}"
                )

            # Handle 404 Not Found
            elif response.status_code == 404:
                return f"❌ Error: Issue {issue_key} does not exist or you lack permission to view it."
            
            # Handle other HTTP errors (401, 403, 500, etc.)
            else:
                return f"❌ Jira API Error (HTTP {response.status_code}): {response.text[:200]}"

    except httpx.ConnectError:
        return "❌ Network Error: Could not connect to the Jira host. Check your JIRA_URL."
    except Exception as e:
        return f"❌ System Error: {str(e)}"

app = mcp.http_app()

if __name__ == "__main__":
    # This allows you to run the server with: uv run python jira_server.py
    mcp.run()
