from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from fastapi import FastAPI, Query
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = FastAPI()

def get_user_events(access_token: str, time_min: str, time_max: str):
    """Fetch all events for a user across all their calendars."""
    credentials = google.oauth2.credentials.Credentials(access_token)
    service = build("calendar", "v3", credentials=credentials)
    
    # Get all calendars
    calendar_list = service.calendarList().list().execute()
    calendar_ids = [cal["id"] for cal in calendar_list.get("items", [])]
    
    # Fetch events for each calendar
    all_events = []
    for cal_id in calendar_ids:
        events = (
            service.events()
            .list(
                calendarId=cal_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
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
