
import os
from collections import defaultdict

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "ak_oxk9pbvonfj3e9z8l8gecico"


class AnalyticsRequest(BaseModel):
    events: list[dict[str, Any]]


@app.get("/")
def home():
    return {"status": "ok", "service": "Q7 Analytics API"}


@app.post("/analytics")
def analytics(
    body: AnalyticsRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = os.environ.get("USER_EMAIL", "").strip()
    if not email:
        raise HTTPException(
            status_code=500,
            detail="Set the USER_EMAIL environment variable",
        )

    events = body.events
    user_totals = defaultdict(float)
    revenue = 0.0

    for event in events:
        user = event.get("user")
        amount = event.get("amount", 0)

        if not isinstance(user, str):
            raise HTTPException(
                status_code=400,
                detail="Each event must have a string user",
            )

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Each event must have a numeric amount",
            )

        if amount > 0:
            revenue += amount
            user_totals[user] += amount

    top_user = max(user_totals, key=user_totals.get) if user_totals else None

    return {
        "email": email,
        "total_events": len(events),
        "unique_users": len(set(event["user"] for event in events)),
        "revenue": round(revenue, 10),
        "top_user": top_user,
    }
