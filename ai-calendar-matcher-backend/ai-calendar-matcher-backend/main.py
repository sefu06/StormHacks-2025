# main.py
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

app = FastAPI(title="Calendar Availability API")


# ------------------------
# 1. LOGIN / AUTH
# ------------------------
@app.get("/login")
def login():
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=https://www.googleapis.com/auth/calendar.readonly"
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
def auth_callback(code: str):
    import requests
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    resp = requests.post(token_url, data=data).json()
    return resp


# ------------------------
# 2. CALENDAR HELPERS
# ------------------------
def get_user_events(access_token, refresh_token, start_iso, end_iso):
    """Fetch calendar events between start and end times."""
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    if not creds.valid:
        creds.refresh(Request())

    service = build("calendar", "v3", credentials=creds)

    calendar_list = service.calendarList().list().execute()
    all_events = []
    for cal in calendar_list.get("items", []):
        events = service.events().list(
            calendarId=cal["id"],
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        all_events.extend(events.get("items", []))
    return all_events


def convert_to_busy_intervals(events):
    busy = []
    for event in events:
        start = event["start"].get("dateTime") or event["start"].get("date")
        end = event["end"].get("dateTime") or event["end"].get("date")
        busy.append((datetime.fromisoformat(start), datetime.fromisoformat(end)))
    return sorted(busy)


def merge_busy_intervals(list_of_busy_intervals):
    """Combine busy intervals across all users."""
    all_busy = sorted([i for sublist in list_of_busy_intervals for i in sublist])
    merged = []
    for start, end in all_busy:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def get_free_intervals(merged_busy, start_day, end_day):
    """Return the time windows where everyone is free."""
    free = []
    current = start_day
    for busy_start, busy_end in merged_busy:
        if current < busy_start:
            free.append((current, busy_start))
        current = max(current, busy_end)
    if current < end_day:
        free.append((current, end_day))
    return free


# ------------------------
# 3. API ENDPOINTS
# ------------------------

@app.get("/shared_free_time")
def shared_free_time(
    start: str = Query(..., description="Start datetime ISO (e.g. 2025-10-04T09:00:00)"),
    end: str = Query(..., description="End datetime ISO (e.g. 2025-10-04T17:00:00)"),
    users: list[str] = Query(..., description="List of JSON strings {access_token, refresh_token}"),
):
    """
    Calculate shared free time among multiple users.
    """
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    all_users_busy = []
    for user_str in users:
        user = json.loads(user_str)
        access_token = user["access_token"]
        refresh_token = user["refresh_token"]

        events = get_user_events(
            access_token, refresh_token,
            start_dt.isoformat() + "Z", end_dt.isoformat() + "Z"
        )
        busy_intervals = convert_to_busy_intervals(events)
        all_users_busy.append(busy_intervals)

    merged_busy = merge_busy_intervals(all_users_busy)
    free_intervals = get_free_intervals(merged_busy, start_dt, end_dt)

    return {
        "start_range": start_dt.isoformat(),
        "end_range": end_dt.isoformat(),
        "shared_free_time": [
            {"start": s.isoformat(), "end": e.isoformat()}
            for s, e in free_intervals
        ]
    }


@app.get("/user_free_time")
def user_free_time(
    start: str,
    end: str,
    access_token: str,
    refresh_token: str
):
    """
    Return free time for a single user — Gemini can call this
    when it needs each user’s availability separately.
    """
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    events = get_user_events(access_token, refresh_token, start_dt.isoformat()+"Z", end_dt.isoformat()+"Z")
    busy = convert_to_busy_intervals(events)
    merged_busy = merge_busy_intervals([busy])
    free = get_free_intervals(merged_busy, start_dt, end_dt)

    return {
        "free_time": [{"start": s.isoformat(), "end": e.isoformat()} for s, e in free]
    }



@app.get("/env-health")
def env_health():
    return {
        "has_gemini_key": bool(os.getenv("GEMINI_API_KEY")),
        "has_google_client": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
    }

