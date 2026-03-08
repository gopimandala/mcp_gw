import httpx
from fastapi import FastAPI, Request

PROXY_URL = "http://localhost:8000/jira-proxy/jira_lookup"
app = FastAPI()

@app.post("/api/messages")
async def messages(req: Request):
    # 1. Get text directly from the JSON body
    body = await req.json()
    ticket_id = body.get("text", "").strip()

    if not ticket_id:
        return {"reply": "Please provide a ticket ID."}

    # 2. Call the MCP Proxy
    async with httpx.AsyncClient() as client:
        r = await client.post(PROXY_URL, json={"ticket": ticket_id}, timeout=60.0)
        reply = r.json().get("result", "Error retrieving ticket.")
    
    # 3. Return the response immediately
    return {"reply": reply}
