from fastapi import FastAPI, Query
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import router as auth_router
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

app = FastAPI()
app.include_router(auth_router)


# ------------------------
# Calendar helper functions
# ------------------------

def get_user_events(access_token, refresh_token, start_iso, end_iso):
    """Fetch all events for a user across all their calendars, automatically refreshing token."""
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    # Refresh if expired
    if not creds.valid:
        creds.refresh(Request())
        access_token = creds.token

    service = build("calendar", "v3", credentials=creds)

    # Get all calendars
    calendar_list = service.calendarList().list().execute()
    calendar_ids = [cal["id"] for cal in calendar_list.get("items", [])]

    all_events = []
    for cal_id in calendar_ids:
        events = service.events().list(
            calendarId=cal_id,
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
    all_busy = sorted([i for sublist in list_of_busy_intervals for i in sublist])
    merged = []
    for start, end in all_busy:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def get_free_intervals(merged_busy, start_day, end_day):
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
# Endpoints
# ------------------------

@app.get("/shared_free_time")
def shared_free_time(
    start: str = Query(..., description="Start datetime ISO format e.g. 2025-10-04T09:00:00"),
    end: str = Query(..., description="End datetime ISO format e.g. 2025-10-04T17:00:00"),
    users: list[str] = Query(..., description="List of user IDs"),
):
    """
    users: each item is expected to be a stringified JSON object:
        {"access_token": "...", "refresh_token": "..."}
    """
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        all_users_busy = []

        for user_str in users:
            import json
            user = json.loads(user_str)
            access_token = user.get("access_token")
            refresh_token = user.get("refresh_token")
            if not access_token or not refresh_token:
                return {"error": "User must provide both access_token and refresh_token"}

            events = get_user_events(
                access_token,
                refresh_token,
                start_dt.isoformat() + "Z",
                end_dt.isoformat() + "Z"
            )
            busy_intervals = convert_to_busy_intervals(events)
            all_users_busy.append(busy_intervals)

        merged_busy = merge_busy_intervals(all_users_busy)
        free_intervals = get_free_intervals(merged_busy, start_dt, end_dt)

        free_intervals_str = [{"start": s.isoformat(), "end": e.isoformat()} for s, e in free_intervals]
        return {"shared_free_time": free_intervals_str}

    except HttpError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
