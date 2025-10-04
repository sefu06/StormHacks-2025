from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

app = FastAPI()

@app.get("/env-test")
def env_test():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    
    return {
        "client_id": client_id,
        "client_secret": "hidden",  # Don’t expose secrets in real apps
        "redirect_uri": redirect_uri
    }