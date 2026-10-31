import sqlite3
import time


class ReportStore:
    def __init__(self, path):
        self.path = path
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, marker_id TEXT, ward_id TEXT,
                lat REAL, lon REAL, depth_cm REAL, confidence REAL)""")

    def _conn(self):
        return sqlite3.connect(self.path)

    def add(self, marker_id, ward_id, lat, lon, depth_cm, confidence):
        with self._conn() as c:
            c.execute("INSERT INTO reports(ts,marker_id,ward_id,lat,lon,depth_cm,confidence) VALUES(?,?,?,?,?,?,?)",
                      (time.time(), marker_id, ward_id, lat, lon, depth_cm, confidence))

    def recent(self, ward_id, window_min):
        since = time.time() - window_min * 60
        with self._conn() as c:
            return c.execute("SELECT depth_cm, confidence FROM reports WHERE ward_id=? AND ts>=?",
                             (ward_id, since)).fetchall()
