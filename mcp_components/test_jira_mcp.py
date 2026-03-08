#!/usr/bin/env python3
"""
Test Jira MCP client
"""

import asyncio
import httpx
import json

# target_url = "http://127.0.0.1:8011/mcp"
target_url = "http://127.0.0.1:9050/mcp"

jira_issue_key = "KAN-30"

async def test_jira_mcp():
    """Test Jira MCP tool call"""
    
    async with httpx.AsyncClient() as client:
        print("🔗 Connecting to Jira MCP server...")
        
        # Step 1: Get session ID
        response = await client.get(target_url, headers={
            "Accept": "application/json, text/event-stream"
        })
        
        session_id = response.headers.get("mcp-session-id")
        print(f"🔑 Session ID: {session_id[:8]}...")
        
        # Step 2: Initialize session
        print("📋 Initializing Jira MCP session...")
        init_response = await client.post(
            target_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "jira-test-client", "version": "1.0.0"}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            }
        )
        
        print(f"📋 Init status: {init_response.status_code}")
        
        # Step 3: Call get_issue_details
        print("🎫 Getting issue details...")
        call_response = await client.post(
            target_url,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_issue_details",
                    "arguments": {"issue_key": jira_issue_key}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            }
        )
        
        # Parse SSE response
        print(f"📋 Response status: {call_response.status_code}")
        
        if call_response.status_code == 200:
            lines = call_response.text.strip().split('\n')
            for line in lines:
                if line.strip().startswith('data:'):
                    json_data = line.split('data:', 1)[1].strip()
                    try:
                        result = json.loads(json_data)
                        if 'result' in result:
                            structured_result = result.get("result", {}).get("structuredContent", {})
                            actual_result = structured_result.get("result") if isinstance(structured_result, dict) else structured_result
                            print(f"✅ Issue details: {actual_result}")
                        elif 'error' in result:
                            print(f"❌ Server error: {result['error']}")
                        break
                    except json.JSONDecodeError:
                        print("⚠️  Could not parse JSON response")
                        print(f"📋 Raw data: {json_data}")
        else:
            print(f"❌ Tool call failed: {call_response.status_code}")
            print(f"📋 Response: {call_response.text}")

if __name__ == "__main__":
    asyncio.run(test_jira_mcp())
