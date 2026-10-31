import json
import urllib.request

TEMPLATES = {
    "ta": {
        "HIGH": "எச்சரிக்கை: {ward} பகுதியில் வெள்ள நீர் சுமார் {depth} செ.மீ. உயரம். தாழ்வான சாலைகளைத் தவிர்க்கவும்.",
        "MEDIUM": "கவனம்: {ward} பகுதியில் நீர்மட்டம் உயர்கிறது (சுமார் {depth} செ.மீ.). பயணத்தைத் திட்டமிடுங்கள்.",
        "LOW": "{ward} பகுதியில் தற்போது வெள்ள ஆபத்து குறைவு.",
    },
    "en": {
        "HIGH": "WARNING: floodwater about {depth} cm in {ward}. Avoid low-lying roads.",
        "MEDIUM": "CAUTION: water level rising in {ward} (about {depth} cm). Plan your travel.",
        "LOW": "Flood risk is currently low in {ward}.",
    },
}


def build_message(ward_name, level, depth_cm, lang="ta"):
    t = TEMPLATES.get(lang, TEMPLATES["ta"])[level]
    return t.format(ward=ward_name, depth=int(round(depth_cm)) if depth_cm is not None else "?")


class ConsoleNotifier:
    def send(self, ward_id, message):
        print(f"[ALERT {ward_id}] {message}")
        return {"channel": "console", "ok": True}


class WebhookNotifier:
    """POSTs {ward_id, message} as JSON, e.g. to a WhatsApp/SMS gateway of your choice."""

    def __init__(self, url):
        self.url = url

    def send(self, ward_id, message):
        body = json.dumps({"ward_id": ward_id, "message": message}).encode("utf-8")
        req = urllib.request.Request(self.url, body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return {"channel": "webhook", "ok": 200 <= r.status < 300}
