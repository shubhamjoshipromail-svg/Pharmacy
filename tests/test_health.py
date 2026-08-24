from unittest.mock import patch

from fastapi.testclient import TestClient

with patch("sqlalchemy.sql.schema.MetaData.create_all"):
    from app.main import app


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "Drug Interaction Tracker"}
