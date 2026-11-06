import pytest
from fastapi.testclient import TestClient
from keepyourid_verifier.schemas import VerificationResult

from keepyourid.main import app
from keepyourid.modules.credential_verification import router as verification_router
from keepyourid.modules.credential_verification.router import (
    get_credential_verification_service,
)
from keepyourid.modules.credential_verification.service import (
    CredentialVerificationEngineError,
    CredentialVerificationService,
)


class FakeVerifier:
    def __init__(self, result):
        self.result = result

    def verify(self, envelope):
        return self.result


class FailingService:
    def verify(self, signed_credential):
        raise CredentialVerificationEngineError(
            "Credential verification failed unexpectedly."
        )


def make_result(valid=False):
    return VerificationResult(
        valid=valid,
        credential_id="urn:uuid:test",
        issuer="did:ethr:sepolia:0x" + "1" * 40,
        checks={
            "signature": valid,
            "issuer_did": valid,
            "issuer_trust": valid,
            "revocation": True,
            "expiration": True,
        },
        errors=[] if valid else ["Credential signature is invalid."],
    )


def make_envelope(status_list_url=None):
    credential = {
        "id": "urn:uuid:test",
        "issuer": "did:ethr:sepolia:0x" + "1" * 40,
        "validFrom": "2026-01-01T00:00:00+00:00",
        "credentialSubject": {"id": "did:ethr:sepolia:0x" + "2" * 40},
    }

    if status_list_url is not None:
        credential["credentialStatus"] = {
            "type": "BitstringStatusListEntry",
            "statusPurpose": "revocation",
            "statusListIndex": "0",
            "statusListCredential": status_list_url,
        }

    return {
        "credential": credential,
        "proof": {
            "type": "Eip191PersonalSignature",
            "verificationMethod": credential["issuer"] + "#controller",
            "signer": "0x" + "1" * 40,
            "signature": "0x" + "ab" * 65,
        },
    }


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_verification_rate_limit():
    verification_router._verification_hits.clear()
    yield
    verification_router._verification_hits.clear()


def override_service(service):
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_credential_verification_service] = lambda: service
    return previous


def restore_overrides(previous):
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


def test_verify_endpoint_returns_200_for_invalid_credential(client):
    service = CredentialVerificationService(
        verifier=FakeVerifier(make_result(valid=False)),
    )
    previous = override_service(service)

    try:
        response = client.post(
            "/api/v1/verifications",
            json={"signed_credential": make_envelope()},
        )
    finally:
        restore_overrides(previous)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["checks"]["signature"] is False
    assert body["errors"] == ["Credential signature is invalid."]


def test_verify_endpoint_accepts_json_string(client):
    service = CredentialVerificationService(
        verifier=FakeVerifier(make_result(valid=True)),
        allowed_status_list_hosts="issuer.example",
    )
    previous = override_service(service)

    try:
        import json

        response = client.post(
            "/api/v1/verifications",
            json={
                "signed_credential": json.dumps(
                    make_envelope("https://issuer.example/status-lists/issuer")
                )
            },
        )
    finally:
        restore_overrides(previous)

    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_verify_endpoint_rejects_invalid_schema(client):
    response = client.post("/api/v1/verifications", json={})
    assert response.status_code == 422

    response = client.post(
        "/api/v1/verifications",
        json={"signed_credential": []},
    )
    assert response.status_code == 422


def test_verify_endpoint_rejects_malformed_envelope(client):
    service = CredentialVerificationService(verifier=FakeVerifier(make_result()))
    previous = override_service(service)

    try:
        response = client.post(
            "/api/v1/verifications",
            json={"signed_credential": {"credential": {}}},
        )
    finally:
        restore_overrides(previous)

    assert response.status_code == 422


def test_verify_endpoint_rejects_disallowed_status_list_destination(client):
    service = CredentialVerificationService(
        verifier=FakeVerifier(make_result(valid=True)),
        allowed_status_list_hosts="allowed.example",
    )
    previous = override_service(service)

    try:
        response = client.post(
            "/api/v1/verifications",
            json={
                "signed_credential": make_envelope("https://evil.example/status")
            },
        )
    finally:
        restore_overrides(previous)

    assert response.status_code == 422


def test_verify_endpoint_returns_500_without_stack_trace(client):
    previous = override_service(FailingService())

    try:
        response = client.post(
            "/api/v1/verifications",
            json={"signed_credential": make_envelope()},
        )
    finally:
        restore_overrides(previous)

    assert response.status_code == 500
    assert response.json()["detail"] == "Credential verification failed."
    assert "Traceback" not in response.text


def test_verify_endpoint_rejects_oversized_payload(client):
    response = client.post(
        "/api/v1/verifications",
        json={"signed_credential": "x" * (256 * 1024 + 1)},
    )

    assert response.status_code == 422


def test_verify_endpoint_rate_limits_requests(client, monkeypatch):
    monkeypatch.setattr(verification_router, "VERIFICATION_RATE_LIMIT", 2)
    service = CredentialVerificationService(
        verifier=FakeVerifier(make_result(valid=True)),
    )
    previous = override_service(service)

    try:
        for _ in range(2):
            response = client.post(
                "/api/v1/verifications",
                json={"signed_credential": make_envelope()},
            )
            assert response.status_code == 200

        response = client.post(
            "/api/v1/verifications",
            json={"signed_credential": make_envelope()},
        )
    finally:
        restore_overrides(previous)

    assert response.status_code == 429
