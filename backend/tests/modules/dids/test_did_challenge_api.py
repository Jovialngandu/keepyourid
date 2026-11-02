from uuid import uuid4

from fastapi.testclient import TestClient

from keepyourid.main import app
from keepyourid.core.dependencies import get_db


def test_create_did_challenge_api(db_session):
    from tests.modules.dids.test_did_challenge_service import create_did

    did = create_did(db_session)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)

        response = client.post(
            f"/api/v1/dids/{did.id}/challenges",
            json={
                "purpose": "did_authentication",
                "domain": "keepyourid.local",
            },
        )

        assert response.status_code == 201

        payload = response.json()

        assert payload["challenge_id"]
        assert payload["challenge"]
        assert payload["purpose"] == "did_authentication"
        assert payload["domain"] == "keepyourid.local"
        assert payload["expires_at"]

    finally:
        app.dependency_overrides.clear()


def test_create_challenge_for_unknown_did_api(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)

        response = client.post(
            f"/api/v1/dids/{uuid4()}/challenges",
            json={
                "purpose": "did_authentication",
                "domain": "keepyourid.local",
            },
        )

        assert response.status_code == 404

    finally:
        app.dependency_overrides.clear()