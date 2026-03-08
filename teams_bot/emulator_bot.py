import httpx
from fastapi import FastAPI, Request

app = FastAPI()
PROXY_URL = "http://localhost:8000/jira-proxy/jira_lookup"
EMULATOR_PORT = 58723 

@app.post("/api/messages")
async def messages(req: Request):
    try:
        body = await req.json()
        text = body.get("text", "")
        print(f"📥 Received: {text}")

        # 1. Get Jira Data
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(PROXY_URL, json={"ticket": text})
            reply_text = r.json().get("result", "No details found.")

        # 2. Extract routing info (Only if coming from Emulator)
        conv = body.get("conversation", {})
        conv_id = conv.get("id")

        if not conv_id:
            print("⚠️ No conversation ID (likely a curl test)")
            return {"reply": reply_text}

        # 3. Build and send the Emulator reply
        reply_payload = {
            "type": "message",
            "text": str(reply_text),
            "from": {"id": "bot"},
            "recipient": body.get("from"),
            "conversation": conv,
            "replyToId": body.get("id")
        }

        callback_url = f"http://localhost:{EMULATOR_PORT}/v3/conversations/{conv_id}/activities"
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(callback_url, json=reply_payload)
            print(f"📤 Sent to Emulator (Port {EMULATOR_PORT}): {resp.status_code}")

        return {"status": "ok"}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9010)
