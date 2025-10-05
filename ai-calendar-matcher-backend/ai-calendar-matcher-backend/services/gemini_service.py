import os, json
from typing import List
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-1.5-flash"

SCHEMA = {
  "type":"array",
  "items":{
    "type":"object",
    "properties":{
      "windowStart":{"type":"string"},
      "windowEnd":{"type":"string"},
      "title":{"type":"string"},
      "description":{"type":"string"},
      "durationMinutes":{"type":"integer"},
      "estimatedCostPerPerson":{"type":"string","enum":["$","$$","$$$"]},
      "indoorOutdoor":{"type":"string","enum":["indoor","outdoor","either"]},
      "bookingRecommended":{"type":"boolean"},
      "category":{"type":"string"},
      "notes":{"type":"string"}
    },
    "required":["windowStart","windowEnd","title","durationMinutes"],
    "additionalProperties":False
  }
}

def _prompt(location, group_size, budget, preferences, free_windows):
    return (
        "You are a group activity planner.\n"
        "Return ONLY JSON matching the schema. One suggestion per free window.\n"
        f"Location: {location}\nGroup size: {group_size}\nBudget: {budget}\n"
        f"Preferences: {preferences}\nFree windows: {free_windows}\n"
    )

def generate_suggestions(*, location: str, group_size: int, budget: str,
                         preferences: List[str], free_windows: List[dict]) -> List[dict]:
    model = genai.GenerativeModel(
        MODEL,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": SCHEMA,
        },
    )
    resp = model.generate_content(
        _prompt(location, group_size, budget, preferences, free_windows)
    )
    try:
        return json.loads(resp.text)
    except Exception:
        return []
