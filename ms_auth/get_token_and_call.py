import os
from dotenv import load_dotenv
import msal
import requests

# Load .env
load_dotenv()

CLIENT_ID = os.getenv("APP_CLIENT_ID")
TENANT_ID = os.getenv("APP_TENANT_ID")

if not CLIENT_ID or not TENANT_ID:
    raise ValueError("Missing APP_CLIENT_ID or APP_TENANT_ID in .env")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = [f"api://{CLIENT_ID}/access_as_user"]

# Create MSAL app
app = msal.PublicClientApplication(
    CLIENT_ID,
    authority=AUTHORITY
)

# Step 1: Start device code flow
flow = app.initiate_device_flow(scopes=SCOPE)

if "user_code" not in flow:
    raise Exception(f"Failed to create device flow: {flow}")

print("\n👉 Go to:", flow["verification_uri"])
print("👉 Enter code:", flow["user_code"])

# Step 2: Wait for login
result = app.acquire_token_by_device_flow(flow)

if "access_token" not in result:
    raise Exception(f"Failed to get token: {result}")

access_token = result["access_token"]

print("\n✅ Got access token")

import jwt

decoded = jwt.decode(access_token, options={"verify_signature": False})
print("\nTOKEN CLAIMS:\n", decoded)

# Step 3: Call your FastAPI API
headers = {
    "Authorization": f"Bearer {access_token}"
}

# Test /secure endpoint
resp = requests.get("http://127.0.0.1:8000/secure", headers=headers)

print("\n--- /secure ---")
print(resp.status_code)
print(resp.text)

# Test /delete endpoint
resp2 = requests.post("http://127.0.0.1:8000/delete", headers=headers)

print("\n--- /delete ---")
print(resp2.status_code)
print(resp2.text)