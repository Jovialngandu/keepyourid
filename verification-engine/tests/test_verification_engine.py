import base64
import hashlib
import json

import pytest
from eth_keys import keys

from keepyourid.modules.credentials.cryptography.jws import b64url_encode, build_signing_input, complete_jws
from keepyourid.verification.interfaces import ResolvedDID
from verification_engine.engine import VerificationEngineError, verify_credential


class FakeResolver:
    def __init__(self, document):
        self.document = document

    def resolve(self, did):
        return ResolvedDID(did=did, document=self.document, metadata={})


@pytest.fixture
def issuer_material():
    private_key = keys.PrivateKey(b"\x11" * 32)
    did = f"did:ethr:sepolia:{private_key.public_key.to_checksum_address()}"
    key_id = f"{did}#controller"
    public_key_hex = private_key.public_key.to_hex()
    document = {
        "id": did,
        "verificationMethod": [
            {
                "id": key_id,
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": did,
                "publicKeyHex": public_key_hex,
            }
        ],
        "authentication": [key_id],
        "assertionMethod": [key_id],
    }
    return private_key, did, key_id, document


def test_verify_credential_success(issuer_material):
    private_key, did, key_id, document = issuer_material

    payload = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:123",
        "type": ["VerifiableCredential", "UniversityDegreeCredential"],
        "issuer": did,
        "validFrom": "2026-11-03T00:00:00+00:00",
        "credentialSubject": {"id": "did:example:holder"},
    }
    signing_input = build_signing_input(payload, key_id)
    digest = hashlib.sha256(signing_input.encode("ascii")).digest()
    signature = private_key.sign_msg_hash(digest)
    token = complete_jws(signing_input, b64url_encode(signature[:-1]))

    result = verify_credential(token, resolver=FakeResolver(document))

    assert result.valid is True
    assert result.status == "valid"
    assert result.issuer == did
    assert result.verification_method == key_id
    assert result.error is None


def test_verify_credential_rejects_modified_payload(issuer_material):
    private_key, did, key_id, document = issuer_material

    payload = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:123",
        "type": ["VerifiableCredential", "UniversityDegreeCredential"],
        "issuer": did,
        "validFrom": "2026-11-03T00:00:00+00:00",
        "credentialSubject": {"id": "did:example:holder"},
    }
    signing_input = build_signing_input(payload, key_id)
    digest = hashlib.sha256(signing_input.encode("ascii")).digest()
    signature = private_key.sign_msg_hash(digest)
    token = complete_jws(signing_input, b64url_encode(signature[:-1]))

    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    result = verify_credential(tampered, resolver=FakeResolver(document))

    assert result.valid is False
    assert result.status == "invalid"
    assert "Invalid credential signature" in (result.error or "") or "Cryptographic verification failed" in (result.error or "")


def test_verify_credential_rejects_unknown_issuer_or_missing_public_key(issuer_material):
    _, did, key_id, _ = issuer_material
    document = {
        "id": did,
        "verificationMethod": [
            {
                "id": key_id,
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": did,
            }
        ],
        "authentication": [key_id],
        "assertionMethod": [key_id],
    }

    result = verify_credential(
        "header.payload.signature",
        resolver=FakeResolver(document),
    )

    assert result.valid is False
    assert result.status == "invalid"
    assert any(
        fragment in (result.error or "").lower()
        for fragment in [
            "invalid compact jws format",
            "invalid start byte",
            "key is missing",
            "credential input must be",
        ]
    )


def test_verify_credential_rejects_invalid_signature(issuer_material):
    private_key, did, key_id, document = issuer_material

    payload = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "id": "urn:uuid:456",
        "type": ["VerifiableCredential", "UniversityDegreeCredential"],
        "issuer": did,
        "validFrom": "2026-11-03T00:00:00+00:00",
        "credentialSubject": {"id": "did:example:holder"},
    }
    signing_input = build_signing_input(payload, key_id)
    digest = hashlib.sha256(signing_input.encode("ascii")).digest()
    signature = keys.PrivateKey(b"\x22" * 32).sign_msg_hash(digest)
    token = complete_jws(signing_input, b64url_encode(signature[:-1]))

    result = verify_credential(token, resolver=FakeResolver(document))

    assert result.valid is False
    assert result.status == "invalid"
    assert "Invalid credential signature" in (result.error or "") or "Cryptographic verification failed" in (result.error or "")
