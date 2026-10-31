import cv2
import pytest
from fastapi.testclient import TestClient
from neer_kaaval.api import create_app
from neer_kaaval.synthetic import make_marker_image

LAT, LON = 12.9816, 80.2181  # M-VEL-001


@pytest.fixture()
def client(tmp_path):
    return TestClient(create_app(db_path=str(tmp_path / "t.db")))


def png(depth):
    return cv2.imencode(".png", make_marker_image(depth))[1].tobytes()


def post(client, depth, marker="M-VEL-001", lat=LAT, lon=LON):
    return client.post("/reports", data={"marker_id": marker, "lat": lat, "lon": lon},
                       files={"image": ("m.png", png(depth), "image/png")})


def test_report_updates_ward_risk(client):
    for d in (52, 55):
        assert abs(post(client, d).json()["depth_cm"] - d) <= 5
    r = client.get("/wards/W-VEL/risk").json()
    assert r["level"] == "HIGH" and r["reports_used"] == 2 and not r["low_confidence"]


def test_geofence_and_unknown_marker(client):
    assert post(client, 20, lat=13.5, lon=80.9).status_code == 422
    assert post(client, 20, marker="NOPE").status_code == 404


def test_tamil_alert_text(client):
    post(client, 55)
    a = client.get("/alerts/W-VEL?lang=ta").json()
    assert "வேளச்சேரி" in a["message"] and a["level"] == "HIGH"
    assert client.post("/alerts/W-VEL/send").json()["delivery"]["ok"]
