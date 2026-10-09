"""Peak-foliage timing from latitude and calendar date. No network."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

# Northern-hemisphere rule of thumb, aligned with typical US peak maps:
# ~42°N (Boston / Chicago) peaks around Oct 12 (day 285).
# Roughly 3.8 days later per degree south.
PEAK_DOY_AT_42N = 285
DAYS_PER_DEGREE = 3.8


def peak_doy(lat: float) -> float:
    lat = max(24.0, min(62.0, lat))
    return PEAK_DOY_AT_42N + (42.0 - lat) * DAYS_PER_DEGREE


def stage_for(lat: float, when: date | None = None) -> dict[str, Any]:
    when = when or datetime.now(timezone.utc).date()
    doy = when.timetuple().tm_yday
    peak = peak_doy(lat)
    delta = doy - peak  # negative = before peak

    if delta < -21:
        stage = "green"
        headline = "Canopy still holding summer"
        look_for = "Look for the first yellow on birch and ash, usually on sun-facing edges."
        color = "#6b8f4e"
    elif delta < -10:
        stage = "early"
        headline = "Early color, edges first"
        look_for = "Maples lighting at the crown. Sumac and Virginia creeper already loud along fences."
        color = "#c9a227"
    elif delta < -3:
        stage = "near-peak"
        headline = "Near peak — go this week"
        look_for = "Sugar maple going gold-to-scarlet from the top down. Walk a ridge if you can."
        color = "#c45c26"
    elif delta <= 7:
        stage = "peak"
        headline = "Peak color"
        look_for = "Full canopy fire. Oaks still greener underneath; look up, then look at the ground for the first leaf carpets."
        color = "#c45c26"
    elif delta <= 18:
        stage = "late"
        headline = "Late color — oaks and beech"
        look_for = "Maples are dropping. Oaks go russet and bronze; beech holds pale gold. Best light is late afternoon."
        color = "#8a4b2a"
    else:
        stage = "bare"
        headline = "Most leaves down"
        look_for = "Structure season: bark, seed heads, sky through branches. Evergreens and the last oak leaves still count."
        color = "#5c5346"

    start = date(when.year, 1, 1).toordinal()
    peak_date = date.fromordinal(start + min(365, max(1, int(round(peak)))) - 1)

    return {
        "stage": stage,
        "headline": headline,
        "look_for": look_for,
        "color": color,
        "days_from_peak": round(delta, 1),
        "peak_date": peak_date.isoformat(),
        "latitude": round(lat, 4),
        "today": when.isoformat(),
    }
