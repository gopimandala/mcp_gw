#!/usr/bin/env python3

from fastapi import FastAPI
import httpx
import json

app = FastAPI()

MCP_URL = "http://127.0.0.1:8020/mcp"

SESSION_ID = None

async def get_session(client: httpx.AsyncClient):
    """
    Create MCP session and initialize protocol
    """
    global SESSION_ID

    if SESSION_ID:
        return SESSION_ID

    print("🔗 Creating MCP session...")

    # Step 1: Create session
    r = await client.get(
        MCP_URL,
        headers={
            "Accept": "application/json, text/event-stream"
        }
    )

    SESSION_ID = r.headers.get("mcp-session-id")

    if not SESSION_ID:
        raise Exception("Failed to obtain MCP session")

    print(f"🔑 Session created: {SESSION_ID}")

    # Step 2: Initialize protocol
    init_response = await client.post(
        MCP_URL,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-proxy",
                    "version": "1.0"
                }
            }
        },
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": SESSION_ID
        }
    )

    print("📋 MCP initialize status:", init_response.status_code)

    return SESSION_ID


def parse_sse_response(text: str):
    """
    Extract JSON payload from SSE response
    """
    lines = text.strip().split("\n")

    for line in lines:
        if line.startswith("data:"):
            try:
                data = json.loads(line[5:].strip())
                return data
            except Exception:
                pass

    return {"error": "Could not parse SSE response"}


@app.post("/jira_lookup")
async def jira_lookup(payload: dict):
    """
    Proxy endpoint for Jira MCP tool
    """

    ticket = payload.get("ticket")

    if not ticket:
        return {"error": "ticket field required"}

    async with httpx.AsyncClient(timeout=60) as client:

        session_id = await get_session(client)

        print(f"🎫 Looking up issue: {ticket}")

        r = await client.post(
            MCP_URL,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_issue_details",
                    "arguments": {
                        "issue_key": ticket
                    }
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            }
        )

        print("📋 Tool call status:", r.status_code)
        print("📋 Tool call response:", r.text)

        result = parse_sse_response(r.text)
        structured = result["result"]["structuredContent"]
        return {"result": structured["result"]}