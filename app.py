from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from foliage import stage_for
from llm import available_models, pick_model, write_card
from parks import fetch_parks, geocode, load_cached_nearest

ROOT = Path(__file__).parent
STATIC = ROOT / "static"

app = FastAPI(title="Leafwalk")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class PlanRequest(BaseModel):
    lat: float | None = None
    lon: float | None = None
    place: str | None = None
    minutes: int = Field(40, ge=15, le=180)
    mode: str = Field("walk")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/status")
def status() -> dict:
    models = available_models()
    return {
        "ollama": bool(models),
        "model": pick_model(models),
        "models": models,
        "offline_note": "Park tiles cache to disk after one fetch. Foliage math never needs a network.",
    }


@app.post("/api/plan")
def plan(req: PlanRequest) -> dict:
    lat, lon = req.lat, req.lon
    label = "your location"
    online = True

    if (lat is None or lon is None) and req.place:
        try:
            geo = geocode(req.place.strip())
        except Exception as exc:
            raise HTTPException(502, f"Could not geocode (need a network once): {exc}") from exc
        if not geo:
            raise HTTPException(404, "Place not found")
        lat, lon, label = geo["lat"], geo["lon"], geo["label"]
    elif lat is None or lon is None:
        raise HTTPException(400, "Share a location or type a place")

    foliage = stage_for(lat)
    parks: list = []
    try:
        parks = fetch_parks(lat, lon)
    except Exception:
        online = False
        parks = load_cached_nearest(lat, lon)

    if not parks:
        raise HTTPException(
            503,
            "No parks on disk for this area. Connect once so Leafwalk can cache OpenStreetMap parks, then it works on the trail.",
        )

    # Prefer a park you can actually reach in the time budget (~80 m/min walk, 160 run)
    speed = 160 if req.mode == "run" else 80
    reach = speed * max(8, req.minutes // 3)
    reachable = [p for p in parks if p["distance_m"] <= reach] or parks[:5]
    pick = reachable[0]

    card = write_card(pick, foliage, req.minutes, req.mode if req.mode in {"walk", "run"} else "walk")

    return {
        "label": label,
        "lat": lat,
        "lon": lon,
        "online_fetch": online,
        "foliage": foliage,
        "park": pick,
        "nearby": reachable[:6],
        "minutes": req.minutes,
        "mode": req.mode,
        "card": card,
    }
