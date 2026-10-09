"""Nearby parks and woods from OpenStreetMap, cached on disk for offline walks."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import httpx

CACHE_DIR = Path(__file__).parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

OVERPASS = "https://overpass-api.de/api/interpreter"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

USER_AGENT = "Leafwalk/1.0 (local foliage walk planner; open-source)"


def _cache_key(lat: float, lon: float, radius_m: int) -> Path:
    return CACHE_DIR / f"{round(lat, 3)}_{round(lon, 3)}_{radius_m}.json"


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def geocode(place: str) -> dict[str, float] | None:
    with httpx.Client(timeout=20.0, headers={"User-Agent": USER_AGENT}) as client:
        r = client.get(
            NOMINATIM,
            params={"q": place, "format": "json", "limit": 1},
        )
        r.raise_for_status()
        data = r.json()
    if not data:
        return None
    return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "label": data[0].get("display_name", place)}


def fetch_parks(lat: float, lon: float, radius_m: int = 4000) -> list[dict[str, Any]]:
    cache = _cache_key(lat, lon, radius_m)
    if cache.exists() and time.time() - cache.stat().st_mtime < 60 * 60 * 24 * 14:
        return json.loads(cache.read_text(encoding="utf-8"))

    query = f"""
    [out:json][timeout:25];
    (
      way["leisure"="park"](around:{radius_m},{lat},{lon});
      way["leisure"="nature_reserve"](around:{radius_m},{lat},{lon});
      way["leisure"="garden"](around:{radius_m},{lat},{lon});
      relation["leisure"="park"](around:{radius_m},{lat},{lon});
      way["natural"="wood"](around:{radius_m},{lat},{lon});
      way["landuse"="forest"](around:{radius_m},{lat},{lon});
    );
    out center tags;
    """
    with httpx.Client(timeout=40.0, headers={"User-Agent": USER_AGENT}) as client:
        r = client.post(OVERPASS, data={"data": query})
        r.raise_for_status()
        elements = r.json().get("elements", [])

    parks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for el in elements:
        tags = el.get("tags") or {}
        name = tags.get("name")
        if not name:
            continue
        center = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        if center.get("lat") is None:
            continue
        key = name.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        plat, plon = float(center["lat"]), float(center["lon"])
        kind = tags.get("leisure") or tags.get("natural") or tags.get("landuse") or "park"
        parks.append(
            {
                "name": name,
                "kind": kind,
                "lat": plat,
                "lon": plon,
                "distance_m": round(haversine_m(lat, lon, plat, plon)),
                "trees": tags.get("leaf_type") or tags.get("wood") or "",
                "wikipedia": tags.get("wikipedia") or "",
            }
        )

    parks.sort(key=lambda p: p["distance_m"])
    parks = parks[:24]
    cache.write_text(json.dumps(parks, indent=2), encoding="utf-8")
    return parks


def load_cached_nearest(lat: float, lon: float) -> list[dict[str, Any]]:
    """Use any nearby cache when Overpass is unreachable (trail, no signal)."""
    best: list[dict[str, Any]] | None = None
    best_d = 1e18
    if not CACHE_DIR.exists():
        return []
    for path in CACHE_DIR.glob("*.json"):
        parts = path.stem.split("_")
        if len(parts) < 3:
            continue
        try:
            clat, clon = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        d = haversine_m(lat, lon, clat, clon)
        if d < best_d:
            best_d = d
            best = json.loads(path.read_text(encoding="utf-8"))
    if best is None or best_d > 25000:
        return []
    for p in best:
        p["distance_m"] = round(haversine_m(lat, lon, p["lat"], p["lon"]))
    best.sort(key=lambda p: p["distance_m"])
    return best
