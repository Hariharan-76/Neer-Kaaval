import json
import os
import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .alerts import ConsoleNotifier, WebhookNotifier, build_message
from .conditions import FileConditionsProvider
from .depth import MarkerNotFound, estimate_depth
from .geo import haversine_m
from .risk import consensus_depth, risk_score
from .storage import ReportStore

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(db_path=None, data_dir=None):
    db_path = db_path or os.getenv("NK_DB_PATH", "./neer_kaaval.db")
    data_dir = data_dir or os.getenv("NK_DATA_DIR", os.path.join(ROOT, "data"))
    height = float(os.getenv("NK_MARKER_HEIGHT_CM", "100"))
    bands = int(os.getenv("NK_MARKER_BANDS", "10"))
    geofence = float(os.getenv("NK_GEOFENCE_M", "100"))
    window = float(os.getenv("NK_WINDOW_MIN", "30"))

    def load(n):
        with open(os.path.join(data_dir, n), encoding="utf-8") as f:
            return json.load(f)

    wards = {w["id"]: w for w in load("wards.json")}
    markers = {m["id"]: m for m in load("markers.json")}
    store = ReportStore(db_path)
    conditions = FileConditionsProvider(os.path.join(data_dir, "conditions_sample.json"))
    notifier = WebhookNotifier(os.getenv("NK_WEBHOOK_URL", "")) if os.getenv("NK_NOTIFIER") == "webhook" else ConsoleNotifier()

    app = FastAPI(title="Neer Kaaval", version="0.1.0")

    def ward_status(ward_id):
        w = wards[ward_id]
        depth, n = consensus_depth(store.recent(ward_id, window))
        rain, res = conditions.get(ward_id)
        score, level = risk_score(depth, rain, res)
        return {"ward_id": ward_id, "name": w["name"], "name_ta": w["name_ta"], "lat": w["lat"], "lon": w["lon"],
                "depth_cm": depth, "reports_used": n, "rainfall_mm_3h": rain, "reservoir_level_pct": res,
                "score": score, "level": level, "low_confidence": n < 2}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/wards")
    def all_wards():
        return [ward_status(w) for w in wards]

    @app.get("/wards/{ward_id}/risk")
    def ward_risk(ward_id: str):
        if ward_id not in wards:
            raise HTTPException(404, "unknown ward")
        return ward_status(ward_id)

    @app.post("/reports")
    async def submit_report(marker_id: str = Form(...), lat: float = Form(...), lon: float = Form(...),
                            image: UploadFile = File(...)):
        m = markers.get(marker_id)
        if not m:
            raise HTTPException(404, "unknown marker")
        dist = haversine_m(lat, lon, m["lat"], m["lon"])
        if dist > geofence:
            raise HTTPException(422, f"photo location is {dist:.0f} m from marker (limit {geofence:.0f} m)")
        img = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(422, "could not decode image")
        try:
            r = estimate_depth(img, height, bands)
        except MarkerNotFound as e:
            raise HTTPException(422, f"marker not detected: {e}")
        store.add(marker_id, m["ward_id"], lat, lon, r.depth_cm, r.confidence)
        return {"ward_id": m["ward_id"], "depth_cm": r.depth_cm, "confidence": r.confidence}

    @app.get("/alerts/{ward_id}")
    def alert_text(ward_id: str, lang: str = "ta"):
        if ward_id not in wards:
            raise HTTPException(404, "unknown ward")
        s = ward_status(ward_id)
        name = s["name_ta"] if lang == "ta" else s["name"]
        return {"ward_id": ward_id, "level": s["level"], "message": build_message(name, s["level"], s["depth_cm"], lang)}

    @app.post("/alerts/{ward_id}/send")
    def send_alert(ward_id: str, lang: str = "ta"):
        a = alert_text(ward_id, lang)
        return {**a, "delivery": notifier.send(ward_id, a["message"])}

    @app.get("/")
    def index():
        return FileResponse(os.path.join(ROOT, "static", "index.html"))

    return app


app = create_app() if os.getenv("NK_AUTOCREATE", "1") == "1" else None
