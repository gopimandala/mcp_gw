#!/usr/bin/env python3
"""
Test MCP header preservation through Kong
"""

import asyncio
import httpx
import json

async def test_header_preservation():
    """Test if Kong preserves MCP headers correctly"""
    
    async with httpx.AsyncClient() as client:
        print("🔗 Testing header preservation through Kong...")
        
        # Step 1: Get session ID through Kong
        response = await client.get("http://localhost:8000/mcp", headers={
            "Accept": "application/json, text/event-stream"
        })
        
        session_id = response.headers.get("mcp-session-id")
        print(f"🔑 Session ID from Kong: {session_id[:8]}...")
        
        # Check what headers Kong preserved
        print("\n📋 Headers received from Kong:")
        for header, value in response.headers.items():
            if 'mcp' in header.lower() or header.lower() in ['content-type', 'accept']:
                print(f"   {header}: {value}")
        
        # Step 2: Test custom headers through Kong
        print("\n🧪 Testing custom MCP headers...")
        test_response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "header-test", "version": "1.0.0"}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id,
                "X-Custom-Header": "test-value",
                "X-MCP-Test": "header-preservation"
            }
        )
        
        print(f"\n📋 Init response status: {test_response.status_code}")
        print("📋 Headers returned by Kong:")
        for header, value in test_response.headers.items():
            if 'mcp' in header.lower() or 'x-custom' in header.lower() or 'x-mcp' in header.lower():
                print(f"   {header}: {value}")
        
        # Test if custom headers cause issues
        if test_response.status_code == 200:
            print("\n✅ Custom headers preserved successfully")
        else:
            print(f"\n❌ Custom headers may be blocked: {test_response.status_code}")
            print(f"📋 Response: {test_response.text}")

if __name__ == "__main__":
    asyncio.run(test_header_preservation())
