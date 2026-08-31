"""Fluxo de ponta a ponta pela API (usado como evidência do protótipo funcional)."""
from fastapi.testclient import TestClient

from app.main import app


def test_full_demo_flow(db_session):
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200

        r = client.post("/allocation/generate", json={"user": "coordenador-geral"})
        assert r.status_code == 200
        run = r.json()
        assert run["teams_allocated"] > 0
        assert run["violations"] == 0

        r = client.get("/metrics/dashboard")
        assert r.status_code == 200
        assert r.json()["total_rooms"] > 0

        r = client.get("/metrics/comparison")
        assert r.status_code == 200
        body = r.json()
        assert body["before"] is not None and body["after"] is not None

        r = client.get("/metrics/engine")
        assert r.status_code == 200

        first_run = client.get("/allocation/runs").json()[0]
        accepted = next(a for a in first_run["assignments"] if a["room_id"] is not None)
        r = client.post(
            "/allocation/override",
            json={"assignment_id": accepted["id"], "action": "ACCEPT", "user": "coordenador-geral"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "accepted"

        r = client.get("/audit")
        assert r.status_code == 200
        assert len(r.json()) > 0
