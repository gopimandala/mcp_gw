import httpx
import asyncio

URL = "http://localhost:8020/mcp"

async def test_jira():
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": "get_issue_details",
            "arguments": {
                "issue_key": "KAN-999"
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(URL, json=payload, headers=headers)

    print("Status:", response.status_code)
    print("Response:", response.text)

asyncio.run(test_jira())