# Leafwalk — Touch Grass

The screen is the shortest part of the walk.

Leafwalk plans a foliage walk from your location and then gets out of the way. You get a trailhead card: a nearby park from OpenStreetMap, whether color is early / peak / late for your latitude this week, and one short paragraph of what to look at. Then trail mode is just a clock and “look at the canopy.” Pocket the phone.

**What is open, and why it matters**

- Foliage timing is a local function of latitude and date. No weather vendor, no account.
- Parks come from OpenStreetMap and cache to disk. Cache once while you have signal; the next walk can happen on a trail with none.
- If Ollama is running, the card is written by an open-weight model on the laptop (Llama 3.2 3B). Your coordinates never go to a cloud LLM.
- Swap the model if you want a different voice. Running it costs nothing.

A closed “ask the assistant where to walk” flow keeps you in chat, needs a network in the woods, and ships your location to someone else’s server. Leafwalk is worse at chatting and better at leaving.

Take it outside: plan at the door, start trail mode, do not unlock until you are back.
