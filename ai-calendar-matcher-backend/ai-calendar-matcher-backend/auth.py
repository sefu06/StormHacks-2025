from fastapi import APIRouter, Request
from fastapi import Query
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import os
import google_auth_oauthlib.flow
from calendar_utils import get_user_events

load_dotenv()

router = APIRouter()

@router.get("/calendar")
def calendar(access_token: str = Query(...)):
    events = get_calendar_events(access_token)
    return {"events": events}

@router.get("/calendar")
def calendar(access_token: str = Query(...)):
    events = get_calendar_events(access_token)
    return JSONResponse(content={"events": events})

# Load credentials from .env
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Login endpoint → redirect to Google OAuth consent
@router.get("/login")
def login():
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return RedirectResponse(auth_url)

# Callback endpoint → Google redirects here after user consent
@router.get("/auth/callback")
def callback(request: Request, code: str = None):
    if code is None:
        return {"error": "No code provided by Google"}

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=code)
    credentials = flow.credentials

    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expires_in": credentials.expiry.isoformat()
    }
