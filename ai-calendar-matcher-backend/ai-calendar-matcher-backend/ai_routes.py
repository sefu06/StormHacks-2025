# ai_routes.py
from typing import List, Literal
from fastapi import APIRouter
from pydantic import BaseModel, Field
from gemini_service import generate_suggestions

router = APIRouter(prefix="/ai", tags=["ai"])

class FreeWindow(BaseModel):
    start: str
    end: str

class SuggestionIn(BaseModel):
    location: str
    groupSize: int = Field(..., ge=1)
    budget: Literal["low","medium","high"] = "medium"
    preferences: List[str] = []
    freeWindows: List[FreeWindow] = []

@router.post("/suggest")
def suggest(body: SuggestionIn):
    return generate_suggestions(
        location=body.location,
        group_size=body.groupSize,
        budget=body.budget,
        preferences=body.preferences,
        free_windows=[w.model_dump() for w in body.freeWindows],
    )
