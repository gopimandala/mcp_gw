#!/usr/bin/env python3
"""
Simple MCP client test - direct tool call to Jira server
"""

import asyncio
import httpx
import json

async def test_mcp_direct():
    """Direct MCP tool call with initialization"""
    
    async with httpx.AsyncClient() as client:
        print("🔗 Establishing SSE connection...")
        
        # Step 1: Get session ID
        response = await client.get("http://127.0.0.1:8011/mcp", headers={
            "Accept": "application/json, text/event-stream"
        })
        
        session_id = response.headers.get("mcp-session-id")
        print(f"🔑 Session ID: {session_id[:8]}...")
        
        # Step 2: Initialize session
        print("📋 Initializing MCP session...")
        init_response = await client.post(
            "http://127.0.0.1:8011/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            }
        )
        
        print(f"📋 Init status: {init_response.status_code}")
        
        # Step 3: Direct tool call
        print("🎫 Calling get_issue_details tool...")
        call_response = await client.post(
            "http://127.0.0.1:8011/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_issue_details",
                    "arguments": {"issue_key": "TEST-123"}
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
        print(f"📋 Response content: {call_response.text}")
        
        if call_response.status_code == 200:
            # Parse SSE format: event: message\ndata: {...}
            lines = call_response.text.strip().split('\n')
            for line in lines:
                # Remove 'data:' prefix with any surrounding whitespace
                if line.strip().startswith('data:'):
                    json_data = line.split('data:', 1)[1].strip()
                    try:
                        result = json.loads(json_data)
                        if 'result' in result:
                            # Direct access to structured content
                            structured_result = result.get("result", {}).get("structuredContent", {})
                            actual_result = structured_result.get("result") if isinstance(structured_result, dict) else structured_result
                            print(f"✅ Jira issue result: {actual_result}")
                        elif 'error' in result:
                            print(f"❌ Server error: {result['error']}")
                        break
                    except json.JSONDecodeError:
                        print("⚠️  Could not parse JSON response")
                        print(f"📋 Raw data: {json_data}")
        else:
            print(f"❌ Tool call failed: {call_response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_mcp_direct())
