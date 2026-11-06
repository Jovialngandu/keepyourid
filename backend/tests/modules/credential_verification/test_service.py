import json

import pytest
from keepyourid_verifier.schemas import VerificationResult

from keepyourid.modules.credential_verification.service import (
    CredentialVerificationEngineError,
    CredentialVerificationService,
    CredentialVerificationValidationError,
)


class FakeVerifier:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.envelope = None

    def verify(self, envelope):
        self.envelope = envelope

        if self.error is not None:
            raise self.error

        return self.result


def make_result(
    *,
    valid=True,
    credential_id="urn:uuid:test",
    issuer="did:ethr:sepolia:0x" + "1" * 40,
    checks=None,
    errors=None,
):
    return VerificationResult(
        valid=valid,
        credential_id=credential_id,
        issuer=issuer,
        checks=checks
        or {
            "signature": True,
            "issuer_did": True,
            "issuer_trust": True,
            "revocation": True,
            "expiration": True,
        },
        errors=errors or [],
    )


def make_envelope(status_list_url="https://issuer.example/status-lists/issuer"):
    credential = {
        "id": "urn:uuid:test",
        "type": ["VerifiableCredential", "IdentityCredential"],
        "issuer": "did:ethr:sepolia:0x" + "1" * 40,
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "validFrom": "2026-01-01T00:00:00+00:00",
        "credentialSubject": {"id": "did:ethr:sepolia:0x" + "2" * 40},
    }

    if status_list_url is not None:
        credential["credentialStatus"] = {
            "id": f"{status_list_url}#0",
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


def test_verify_accepts_structured_envelope():
    verifier = FakeVerifier(result=make_result())
    service = CredentialVerificationService(
        verifier=verifier,
        allowed_status_list_hosts="issuer.example",
    )

    result = service.verify(make_envelope())

    assert result["valid"] is True
    assert result["credential_id"] == "urn:uuid:test"
    assert verifier.envelope["credential"]["issuer"].startswith("did:ethr:sepolia:")


def test_verify_accepts_json_string():
    verifier = FakeVerifier(result=make_result(valid=False, errors=["bad"]))
    service = CredentialVerificationService(
        verifier=verifier,
        allowed_status_list_hosts="issuer.example",
    )

    result = service.verify(json.dumps(make_envelope()))

    assert result["valid"] is False
    assert verifier.envelope["proof"]["type"] == "Eip191PersonalSignature"


def test_revoked_credential_result_is_returned():
    verifier = FakeVerifier(
        result=make_result(
            valid=False,
            checks={
                "signature": True,
                "issuer_did": True,
                "issuer_trust": True,
                "revocation": False,
                "expiration": True,
            },
            errors=["Credential has been revoked."],
        )
    )
    service = CredentialVerificationService(
        verifier=verifier,
        allowed_status_list_hosts="issuer.example",
    )

    result = service.verify(make_envelope(status_list_url=None))

    assert result["valid"] is False
    assert result["checks"]["revocation"] is False
    assert result["errors"] == ["Credential has been revoked."]


def test_invalid_signature_result_is_returned():
    verifier = FakeVerifier(
        result=make_result(
            valid=False,
            checks={
                "signature": False,
                "issuer_did": False,
                "issuer_trust": False,
                "revocation": True,
                "expiration": True,
            },
            errors=["Credential signature is invalid."],
        )
    )
    service = CredentialVerificationService(verifier=verifier)

    result = service.verify(make_envelope(status_list_url=None))

    assert result["valid"] is False
    assert result["checks"]["signature"] is False


def test_unknown_issuer_trust_is_returned_without_blocking():
    verifier = FakeVerifier(
        result=make_result(
            valid=True,
            checks={
                "signature": True,
                "issuer_did": True,
                "issuer_trust": "unknown",
                "revocation": True,
                "expiration": True,
            },
            errors=["Issuer registry configuration is missing."],
        )
    )
    service = CredentialVerificationService(
        verifier=verifier,
        allowed_status_list_hosts="issuer.example",
    )

    result = service.verify(make_envelope())

    assert result["valid"] is True
    assert result["checks"]["issuer_trust"] == "unknown"
    assert result["errors"] == ["Issuer registry configuration is missing."]


def test_malformed_envelope_is_rejected():
    verifier = FakeVerifier(result=make_result())
    service = CredentialVerificationService(verifier=verifier)

    with pytest.raises(CredentialVerificationValidationError):
        service.verify({"credential": {}})

    with pytest.raises(CredentialVerificationValidationError):
        service.verify("{not-json")

    with pytest.raises(CredentialVerificationValidationError):
        service.verify([])

    assert verifier.envelope is None


def test_engine_exception_is_wrapped():
    verifier = FakeVerifier(error=RuntimeError("engine exploded"))
    service = CredentialVerificationService(
        verifier=verifier,
        allowed_status_list_hosts="issuer.example",
    )

    with pytest.raises(CredentialVerificationEngineError) as exc_info:
        service.verify(make_envelope())

    assert "engine exploded" not in str(exc_info.value)
    assert verifier.envelope is not None


def test_disallowed_status_list_destination_is_rejected_before_engine():
    verifier = FakeVerifier(result=make_result())
    service = CredentialVerificationService(
        verifier=verifier,
        allowed_status_list_hosts="allowed.example",
    )

    with pytest.raises(CredentialVerificationValidationError):
        service.verify(
            make_envelope(status_list_url="https://evil.example/status-list")
        )

    assert verifier.envelope is None


def test_status_list_destination_matching_host_and_port_is_allowed():
    verifier = FakeVerifier(result=make_result())
    service = CredentialVerificationService(
        verifier=verifier,
        allowed_status_list_hosts="localhost:8001",
    )

    result = service.verify(
        make_envelope(status_list_url="http://localhost:8001/status-lists/issuer")
    )

    assert result["valid"] is True
