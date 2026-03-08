#!/usr/bin/env python3
import asyncio
import httpx
import json

async def test_jira_thru_kong():
    # Update to your Kong Gateway address
    KONG_URL = "http://localhost:8000/jira/mcp"
    ISSUE_KEY = "KAN-31"
    
    async with httpx.AsyncClient() as client:
        print("🚀 [1/4] Connecting to Kong...")
        
        # Step 1: Get Session ID
        # FastMCP returns the ID in headers on a GET request
        response = await client.get(KONG_URL, headers={
            "Accept": "application/json, text/event-stream"
        })
        
        session_id = response.headers.get("mcp-session-id")
        if not session_id:
            print("❌ Error: Could not retrieve mcp-session-id from Kong.")
            return
            
        print(f"🔑 Session ID: {session_id[:8]}...")
        
        # Common headers for all subsequent POSTs
        common_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id
        }
        # Use session_id in URL as well to bypass any Kong filtering
        url_with_id = f"{KONG_URL}?session_id={session_id}"

        # Step 2: Initialize Session
        print("📋 [2/4] Initializing session handshake...")
        await client.post(
            url_with_id,
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
            headers=common_headers
        )

        # Step 3: Send "Initialized" Notification (CRITICAL for tool registration)
        print("🔔 [3/4] Sending 'initialized' notification...")
        await client.post(
            url_with_id,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            },
            headers=common_headers
        )
        
        # Give the server a moment to register the tools internally
        await asyncio.sleep(1)

        print("🔍 Checking available tools...")
        list_resp = await client.post(
            url_with_id,
            json={"jsonrpc": "2.0", "id": 99, "method": "tools/list"},
            headers=common_headers
        )
        print(f"📦 Server says tools are: {list_resp.text}")

        # Step 4: Call get_issue_details
        print(f"🎫 [4/4] Calling tool 'get_issue_details' for {ISSUE_KEY}...")
        call_response = await client.post(
            url_with_id,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_issue_details",
                    "arguments": {"issue_key": ISSUE_KEY}
                }
            },
            headers=common_headers
        )
        
        if call_response.status_code == 200:
            # Parse the SSE data lines to find the result
            for line in call_response.text.strip().split('\n'):
                if line.strip().startswith('data:'):
                    try:
                        json_str = line.split('data:', 1)[1].strip()
                        data_json = json.loads(json_str)
                        
                        # Extract the text content from the MCP result
                        result = data_json.get('result', {})
                        content = result.get('content', [])
                        
                        if content and len(content) > 0:
                            raw_text = content[0].get('text', '')
                            clean_text = raw_text.strip()
                            print(f"SUCCESS! Issue Details:{clean_text}")
                            print("-" * 50)
                        elif 'error' in data_json:
                            print(f"❌ Server Error: {data_json['error']}")
                        else:
                            print(f"⚠️ Unexpected format: {data_json}")
                        break
                    except Exception as e:
                        print(f"⚠️ Parsing Error: {e}")
        else:
            print(f"❌ Failed: HTTP {call_response.status_code}")
            print(f"📋 Response: {call_response.text}")

if __name__ == "__main__":
    asyncio.run(test_jira_thru_kong())
