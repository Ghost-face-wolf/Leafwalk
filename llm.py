"""Local open-weight trail cards via Ollama. Falls back to a template if offline."""

from __future__ import annotations

from typing import Any

import httpx

OLLAMA = "http://127.0.0.1:11434"
PREFERRED = (
    "llama3.2:3b",
    "llama3.2",
    "llama3.1:8b",
    "qwen2.5:3b",
    "phi3:mini",
    "phi3",
    "gemma2:2b",
    "mistral",
)


def available_models() -> list[str]:
    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get(f"{OLLAMA}/api/tags")
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def pick_model(models: list[str]) -> str | None:
    names = set(models)
    for pref in PREFERRED:
        if pref in names:
            return pref
        for m in models:
            if m.split(":")[0] == pref.split(":")[0]:
                return m
    return models[0] if models else None


def fallback_card(park: dict[str, Any], foliage: dict[str, Any], minutes: int, mode: str) -> str:
    verb = "Run" if mode == "run" else "Walk"
    return (
        f"{verb} to {park['name']} ({_distance(park)}). "
        f"{foliage['headline']}. {foliage['look_for']} "
        f"Stay out about {minutes} minutes. Do not open another app. "
        f"When you arrive, pocket the phone and look at the canopy first."
    )


def _distance(park: dict[str, Any]) -> str:
    m = park.get("distance_m") or 0
    if m < 1000:
        return f"{m} m from you"
    return f"{m / 1000:.1f} km from you"


def write_card(
    park: dict[str, Any],
    foliage: dict[str, Any],
    minutes: int,
    mode: str,
    model: str | None = None,
) -> dict[str, Any]:
    models = available_models()
    chosen = model if model in models else pick_model(models)

    prompt = f"""Write a trailhead card for someone about to go outside. 70-90 words. Second person. No emojis, hashtags, or marketing. No numbered lists. One short paragraph, then one last sentence that tells them to pocket the phone.

Facts:
- place: {park['name']} ({park.get('kind', 'park')}, {_distance(park)})
- time outside: {minutes} minutes
- move: {mode}
- foliage stage: {foliage['stage']} ({foliage['headline']})
- what to look for: {foliage['look_for']}
- date: {foliage['today']}, typical peak around {foliage['peak_date']}

Do not invent other park names or street directions."""

    if not chosen:
        return {
            "text": fallback_card(park, foliage, minutes, mode),
            "model": None,
            "source": "template",
        }

    try:
        with httpx.Client(timeout=90.0) as client:
            r = client.post(
                f"{OLLAMA}/api/generate",
                json={
                    "model": chosen,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.6, "num_predict": 220},
                },
            )
            r.raise_for_status()
            text = (r.json().get("response") or "").strip()
        if len(text) < 40:
            raise ValueError("short")
        return {"text": text, "model": chosen, "source": "ollama"}
    except Exception:
        return {
            "text": fallback_card(park, foliage, minutes, mode),
            "model": chosen,
            "source": "template",
        }
