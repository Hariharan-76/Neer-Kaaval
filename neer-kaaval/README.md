# Neer Kaaval (நீர் காவல்) – street-level flood early warning in Tamil

Hack for Social Cause · Team **Claude's Plan** · ID **HSC|TN|02732** · Tamil Nadu

Chennai floods street by street, but warnings are city-wide. Neer Kaaval turns a citizen's photo of a
painted **depth marker** into a real-time, street-level water depth, fuses it with rainfall and reservoir
data, and produces a ward-level risk level with **Tamil** (and English) alerts and a live map.

> **Prototype status:** working end-to-end demo with synthetic marker images, sample ward data and
> sample rainfall/reservoir values. It is not yet field-tested. See [Limitations](#limitations).

## How it works
1. A marker (100 cm, 10 square bands, alternating red/blue, red on top) is painted on a pole or wall.
2. A citizen photographs it; the app sends the photo with GPS to `POST /reports`.
3. The server checks the GPS is within `NK_GEOFENCE_M` of the registered marker, then **OpenCV** counts the
   visible bands to estimate depth (`depth = height − visible height`).
4. Recent reports per ward are combined by **consensus** (outliers and low-confidence photos dropped).
5. Consensus depth + rainfall + reservoir level → **risk score and LOW / MEDIUM / HIGH**.
6. Tamil / English alert text is generated and can be sent through a pluggable notifier; the web map shows all wards.

Architecture and design decisions: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Setup
Requires Python 3.10+.

```bash
git clone <your-repo-url> neer-kaaval && cd neer-kaaval
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # optional; defaults work. Export the variables you change.
python scripts/generate_sample_images.py                # (re)creates data/sample_images/*.png
uvicorn neer_kaaval.api:app --reload
```
Open http://127.0.0.1:8000 for the map + upload form, or http://127.0.0.1:8000/docs for the API docs.
The map page loads Leaflet and OpenStreetMap tiles, so it needs internet access.

### Try it
```bash
curl -F marker_id=M-VEL-001 -F lat=12.9816 -F lon=80.2181 \
     -F image=@data/sample_images/marker_depth_55.png http://127.0.0.1:8000/reports
curl http://127.0.0.1:8000/wards/W-VEL/risk
curl "http://127.0.0.1:8000/alerts/W-VEL?lang=ta"
curl -X POST "http://127.0.0.1:8000/alerts/W-VEL/send?lang=ta"
```

### Environment variables
| Variable | Default | Purpose |
|---|---|---|
| `NK_DB_PATH` | `./neer_kaaval.db` | SQLite file for reports |
| `NK_DATA_DIR` | `./data` | folder with `wards.json`, `markers.json`, `conditions_sample.json` |
| `NK_MARKER_HEIGHT_CM` | `100` | physical marker height |
| `NK_MARKER_BANDS` | `10` | number of bands |
| `NK_GEOFENCE_M` | `100` | max photo-to-marker distance (m) |
| `NK_WINDOW_MIN` | `30` | reports newer than this are used for consensus |
| `NK_NOTIFIER` | `console` | `console` or `webhook` |
| `NK_WEBHOOK_URL` | – | target for `webhook` notifier (JSON `{ward_id, message}`) |

## Tests
```bash
python -m pytest -q
```
Covers depth estimation accuracy (±5 cm on synthetic photos at 0–85 cm), consensus/outlier logic, risk
rules, geofence and unknown-marker rejection, and Tamil alert generation through the API.

## Sample data
- `data/wards.json`, `data/markers.json`: three **demo** wards/markers (locations illustrative, not real installations)
- `data/conditions_sample.json`: **sample** rainfall (mm/3h) and reservoir level (%), not live data
- `data/sample_images/`: synthetic marker photos at known depths (0, 15, 30, 55, 80 cm)

## Limitations
- Depth is estimated with classical colour/band analysis on a roughly upright, unobstructed marker. Heavy
  glare, night photos, strong tilt, dirt, or a partly blocked marker reduce accuracy. A fully submerged
  marker is rejected rather than guessed.
- Not yet validated on real flood photos. Risk weights/thresholds in `risk.py` are heuristics to calibrate with authority data.
- Rainfall/reservoir data are read from a sample file; live IMD/Water Resources feeds are an extension point (`conditions.py`).
- No authentication or rate limiting yet; delivery uses a console or generic webhook notifier.
- Tamil alert wording should be reviewed by native speakers and local authorities before public use.

## Roadmap
YOLOv8 marker segmentation for cluttered scenes · live data feeds · WhatsApp/SMS gateway integration ·
Tamil text-to-speech voice alerts · safe-route layer for ambulances · authentication and abuse protection.

## Project layout
```
neer_kaaval/  depth.py risk.py alerts.py conditions.py geo.py storage.py synthetic.py api.py
data/  scripts/  static/  tests/  docs/ARCHITECTURE.md  LICENSE (MIT)
```
