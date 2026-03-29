from fastapi import FastAPI, Request, HTTPException, Depends
from jose import jwt
import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("APP_CLIENT_ID")
TENANT_ID = os.getenv("APP_TENANT_ID")

if not CLIENT_ID or not TENANT_ID:
    raise ValueError("Missing APP_CLIENT_ID or APP_TENANT_ID in .env")

app = FastAPI()

# For personal Microsoft accounts, use the common endpoint
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
jwks = requests.get(JWKS_URL).json()

def get_token_from_header(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    return auth.split(" ")[1]

def validate_token(token: str):
    try:
        header = jwt.get_unverified_header(token)
        print("\nHeader:", header)
        
        # Find the matching key
        key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
        print("Key:", key)
        
        payload = jwt.decode(
            token,
            key,  # Use the key directly as JWK
            algorithms=["RS256"],
            audience=f"api://{CLIENT_ID}",
            issuer=f"https://sts.windows.net/{TENANT_ID}/"
        )
        print("\nPayload:", payload)
        
        # # TEMPORARY: Remove Admin role for testing
        # if "Admin" in payload.get("roles", []):
        #     payload["roles"] = ["User"]  # Change to User role
        #     print("\n🔧 TEMPORARILY CHANGED ROLE TO: User")
        
        return payload
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"invalid_token: {str(e)}")

def get_current_user(request: Request):
    token = get_token_from_header(request)
    return validate_token(token)

def require_role(role: str):
    def checker(request: Request):
        user = get_current_user(request)
        if role not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker

@app.get("/")
async def root():
    return {"message": "Microsoft Account RBAC Demo", "endpoints": ["/", "/secure", "/delete"]}

@app.get("/secure")
async def secure(request: Request):
    user = get_current_user(request)
    return {
        "name": user.get("name"),
        "roles": user.get("roles", []),
        "upn": user.get("upn"),
        "oid": user.get("oid")
    }

@app.post("/delete")
async def delete(request: Request):
    user = require_role("Admin")(request)
    return {"status": "allowed"}