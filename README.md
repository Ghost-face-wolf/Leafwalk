# Leafwalk

A local-first fall foliage walk planner. The screen is a trailhead: thirty seconds to pick a park, then trail mode so the phone stays in your pocket.

Open pieces do the real work:

- **OpenStreetMap** for parks, woods, and nature reserves
- **On-device foliage math** (latitude + date → peak week, no weather API required)
- **Ollama + an open-weight model** (Llama 3.2 3B by default) to write the walk card
- **Disk cache** so a second walk works with no cell signal

Location is used to find a nearby park. It is not sent to a cloud model.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

Optional, for open-weight trail cards:

```bash
ollama pull llama3.2:3b
ollama serve
```

Without Ollama, Leafwalk still plans a real walk from OSM + the foliage engine. The prose falls back to a local template.

## Why open is the product

A closed maps-plus-chatbot stack wants you looking at the phone. Leafwalk is built so it still works when you walk into the woods and lose signal, and so a walk does not require giving a vendor your GPS trail. Swap the Ollama model if you want a quieter or more specific voice. It costs nothing to run after the model is on disk.
