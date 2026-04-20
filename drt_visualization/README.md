# DRT Visualization

Real-time map visualization server for a Demand-Responsive Transit (DRT) shuttle
system. Listens for vehicle state changes in PostgreSQL via `LISTEN/NOTIFY`,
renders the shuttle position, planned route, and boarding/dropping markers on a
Mapbox map, and streams ETA updates to the browser.

## Features

- Real-time shuttle tracking via PostgreSQL `NOTIFY` on the `new_vehicle` channel
- Mapbox GL JS map with animated vehicle marker and route polyline
- ETA popup with status messages ("Boarding in N min", "Arriving in N min", etc.)
- Server-Sent Events (`/stream`) plus HTTP polling (`/data`) endpoints
- POST endpoint (`/shuttle_data`) for the mobile client to publish the active
  shuttle/passenger selection

## Requirements

- Python 3.9+
- PostgreSQL with a `vehicle_kpi` table and a `NOTIFY new_vehicle` trigger
- A Mapbox access token

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and fill in MAPBOX_TOKEN, DB_USER, DB_PASSWORD, ...
```

## Run

```bash
python main.py
```

Then open http://localhost:8050 in a browser. The map stays blank until a
client posts a shuttle selection to `/shuttle_data`. Example payload:

```bash
curl -X POST http://localhost:8050/shuttle_data \
  -H 'Content-Type: application/json' \
  -d '{
    "shuttle_id": "SHUTTLE0001",
    "passengerId": "1",
    "Departure_Latitude": 37.30000,
    "Departure_Longitude": 126.84000,
    "Destination_Latitude": 37.30500,
    "Destination_Longitude": 126.84500,
    "cur_node": "0000",
    "cur_path": ["0000", "0001"],
    "cur_dst": [["0001", "DROPPING", "1"]]
  }'
```

## Data files

- `map_graph_with_vectors.json` — road network graph (nodes, links, per-link
  travel time in seconds). Used to compute ETA.
- `node_coordinates.csv` — mapping from node ID to (lon, lat).

Both files are loaded at startup. Replace them with your own region's data to
deploy elsewhere.

## Expected database schema

Minimal schema expected by `fetch_new_rows()`:

```sql
CREATE TABLE vehicle_kpi (
    currenttime  TEXT,   -- unix seconds as string (cast to double precision)
    shuttle_id   TEXT,
    cur_node     TEXT,
    cur_path     TEXT,   -- python-literal list of node IDs
    cur_dst      TEXT    -- python-literal list of [node, BOARDING/DROPPING, passenger_id]
);
```

A trigger or application process should `NOTIFY new_vehicle` whenever a new row
is inserted.

## Project layout

```
main.py                       Flask server + DB listener + HTML/JS client
map_graph_with_vectors.json   Road network graph
node_coordinates.csv          Node ID -> lon/lat mapping
.env.example                  Template for environment variables
```

## Environment variables

See `.env.example`. All values are read via `python-dotenv` at startup.

| Variable       | Purpose                                    |
| -------------- | ------------------------------------------ |
| `MAPBOX_TOKEN` | Mapbox GL JS access token                  |
| `DB_HOST`      | PostgreSQL host                            |
| `DB_PORT`      | PostgreSQL port                            |
| `DB_NAME`      | Database name                              |
| `DB_USER`      | Database user                              |
| `DB_PASSWORD`  | Database password                          |
| `FLASK_HOST`   | Interface Flask binds to (default 0.0.0.0) |
| `FLASK_PORT`   | Port Flask binds to (default 8050)         |
| `LOG_LEVEL`    | Python logging level (default INFO)        |

## Production note

`main.py` uses Flask's development server. For production, run behind a
production WSGI server such as `gunicorn` or `uwsgi`, e.g.:

```bash
gunicorn -w 1 --threads 4 -b 0.0.0.0:8050 main:app
```

Note that the background DB-listener thread is started from the `__main__`
guard, so a WSGI server will need an equivalent startup hook.

## License

MIT — see `LICENSE`.
