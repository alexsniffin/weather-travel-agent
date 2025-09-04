from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    message: Optional[str] = Field(None, description="Free text like 'from X to Y'")
    origin: Optional[str] = None
    destination: Optional[str] = None
    travel_date: Optional[str] = None


class ChatOut(BaseModel):
    reply: str
    need: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    stops: Optional[List[Dict[str, Any]]] = None
    forecasts: Optional[List[Dict[str, Any]]] = None
