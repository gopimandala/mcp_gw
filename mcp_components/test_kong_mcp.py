#!/usr/bin/env python3
"""
Test MCP client through Kong gateway
"""

import asyncio
import httpx
import json

target_url = "http://localhost:8000/jira/mcp"

async def test_mcp_via_kong():
    """Test MCP tool call through Kong gateway"""
    
    async with httpx.AsyncClient() as client:
        print("🔗 Establishing SSE connection through Kong...")
        
        # Step 1: Get session ID through Kong
        response = await client.get(target_url, headers={
            "Accept": "application/json, text/event-stream"
        })
        
        session_id = response.headers.get("mcp-session-id")
        print(f"🔑 Session ID: {session_id[:8]}...")
        print(f"🌉 Via Kong: {response.headers.get('via', 'No Kong header')}")
        
        # Step 2: Initialize session through Kong
        print("📋 Initializing MCP session through Kong...")
        init_response = await client.post(
            target_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "kong-test-client", "version": "1.0.0"}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            }
        )
        
        print(f"📋 Init status: {init_response.status_code}")
        
        # Step 3: Direct tool call through Kong
        print("🧮 Calling get_issue_details tool through Kong...")
        call_response = await client.post(
            target_url,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_issue_details",
                    "arguments": {"issue_key": "KAN-65"}
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
        print(f"🌉 Kong latency headers:")
        print(f"   - Upstream: {call_response.headers.get('x-kong-upstream-latency', 'N/A')}ms")
        print(f"   - Proxy: {call_response.headers.get('x-kong-proxy-latency', 'N/A')}ms")
        
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
                            print(f"✅ 12 + 8 = {actual_result} (via Kong)")
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
    asyncio.run(test_mcp_via_kong())
