from fastapi.testclient import TestClient
from app import create_app
import os
from dotenv import load_dotenv

# Ensure env vars are loaded
if os.path.exists("app/.env.dev"):
    print("Loading app/.env.dev")
    load_dotenv("app/.env.dev")
elif os.path.exists(".env"):
    print("Loading .env")
    load_dotenv(".env")

# Mock the lifespan to avoid full startup overhead/conflicts if needed?
# Actually TestClient runs lifespan by default.
# But init_data might be heavy.

app = create_app()

def test_get_models():
    print("Starting TestClient...")
    with TestClient(app) as client:
        print("Sending request...")
        response = client.get("/api/v2/ai/models?page=1&page_size=20")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response JSON: {response.json()}")
        except:
            print(f"Response Text: {response.text}")
        
if __name__ == "__main__":
    test_get_models()
