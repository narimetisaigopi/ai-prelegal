from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_signup_signin_and_documents_flow():
    with TestClient(app) as client:
        signup = client.post(
            "/api/auth/signup",
            json={"email": "user@example.com", "password": "password123"},
        )
        assert signup.status_code == 200

        me = client.get("/api/auth/me")
        assert me.status_code == 200

        created = client.post(
            "/api/documents",
            json={
                "title": "Test NDA",
                "doc_type": "Mutual NDA",
                "content": {"party_a": "A", "party_b": "B"},
            },
        )
        assert created.status_code == 200
        doc_id = created.json()["id"]

        fetched = client.get(f"/api/documents/{doc_id}")
        assert fetched.status_code == 200

        listing = client.get("/api/documents")
        assert listing.status_code == 200
        assert len(listing.json()) == 1
