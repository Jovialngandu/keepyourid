from datetime import datetime, timezone

import pytest

from keepyourid.modules.credentials import service as credential_service_module
from keepyourid.modules.credentials.enums import CredentialStatus
from keepyourid.modules.credentials.schemas import CredentialCreate
from keepyourid.modules.credentials.service import (
    CredentialInvalidDataError,
    CredentialService,
)
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization


ISSUER_DID = "did:ethr:sepolia:0x1234567890123456789012345678901234567890"
KEY_ID = f"{ISSUER_DID}#controller"
PUBLIC_KEY = "0x" + "11" * 64


@pytest.fixture
def issuer(db_session):
    organization = Organization(
        legal_name="Test Organization",
        registration_number="TEST-ISSUER-001",
        email="issuer@example.com",
        status=OrganizationStatus.ACTIVE,
    )

    db_session.add(organization)
    db_session.flush()

    did = DID(
        organization_id=organization.id,
        identifier=ISSUER_DID,
        method="ethr",
        document={
            "verificationMethod": [],
            "assertionMethod": [],
        },
        status=DIDStatus.VERIFIED,
    )

    db_session.add(did)
    db_session.commit()
    db_session.refresh(organization)

    return organization


@pytest.fixture
def draft_credential(db_session, issuer):
    service = CredentialService(db_session)

    data = CredentialCreate(
        credential_type="UniversityDegreeCredential",
        subject={
            "id": "did:example:holder",
            "degree": "Computer Science",
        },
        valid_until=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )

    return service.create_draft(issuer.id, data)


@pytest.fixture
def mocked_signing(monkeypatch):
    def resolve_key(self, credential):
        return KEY_ID, PUBLIC_KEY

    def build_input(payload, key_id):
        assert key_id == KEY_ID
        return "header.payload"

    def complete(input_data, signature):
        assert input_data == "header.payload"
        return f"{input_data}.{signature}"

    def verify(token, public_key, expected_key_id):
        assert public_key == PUBLIC_KEY
        assert expected_key_id == KEY_ID
        return True

    monkeypatch.setattr(
        credential_service_module.IssuerKeyResolver,
        "resolve",
        resolve_key,
    )

    monkeypatch.setattr(
        credential_service_module,
        "build_signing_input",
        build_input,
    )

    monkeypatch.setattr(
        credential_service_module,
        "complete_jws",
        complete,
    )

    monkeypatch.setattr(
        credential_service_module,
        "verify_jws",
        verify,
    )


def test_prepare_issuance_success(
    db_session,
    draft_credential,
    mocked_signing,
):
    service = CredentialService(db_session)

    result = service.prepare_issuance(
        draft_credential.id
    )

    assert result["key_id"] == KEY_ID
    assert result["signing_input"] == "header.payload"

    db_session.refresh(draft_credential)

    assert draft_credential.status == CredentialStatus.DRAFT
    assert draft_credential.signed_credential is None


def test_prepare_issuance_rejects_unknown_credential(
    db_session,
):
    from uuid import uuid4

    service = CredentialService(db_session)

    with pytest.raises(CredentialInvalidDataError):
        service.prepare_issuance(uuid4())


def test_complete_issuance_success(
    db_session,
    draft_credential,
    mocked_signing,
):
    service = CredentialService(db_session)

    result = service.complete_issuance(
        credential_id=draft_credential.id,
        signature="valid-signature",
        key_id=KEY_ID,
    )

    assert result.status == CredentialStatus.ISSUED
    assert result.signed_credential == (
        "header.payload.valid-signature"
    )

    assert result.proof["verificationMethod"] == KEY_ID
    assert result.proof["algorithm"] == "ES256K"


def test_complete_issuance_rejects_wrong_key_id(
    db_session,
    draft_credential,
    mocked_signing,
):
    service = CredentialService(db_session)

    with pytest.raises(
        CredentialInvalidDataError,
        match="Signing key does not belong",
    ):
        service.complete_issuance(
            credential_id=draft_credential.id,
            signature="valid-signature",
            key_id="did:example:attacker#key-1",
        )

    db_session.refresh(draft_credential)

    assert draft_credential.status == CredentialStatus.DRAFT
    assert draft_credential.signed_credential is None


def test_complete_issuance_rejects_invalid_signature(
    db_session,
    draft_credential,
    mocked_signing,
    monkeypatch,
):
    def reject_signature(token, public_key, expected_key_id):
        raise credential_service_module.JWSVerificationError(
            "Invalid signature."
        )

    monkeypatch.setattr(
        credential_service_module,
        "verify_jws",
        reject_signature,
    )

    service = CredentialService(db_session)

    with pytest.raises(
        CredentialInvalidDataError,
        match="signature verification failed",
    ):
        service.complete_issuance(
            credential_id=draft_credential.id,
            signature="invalid-signature",
            key_id=KEY_ID,
        )

    db_session.refresh(draft_credential)

    assert draft_credential.status == CredentialStatus.DRAFT
    assert draft_credential.signed_credential is None


def test_complete_issuance_rejects_already_issued_credential(
    db_session,
    draft_credential,
    mocked_signing,
):
    service = CredentialService(db_session)

    service.complete_issuance(
        credential_id=draft_credential.id,
        signature="valid-signature",
        key_id=KEY_ID,
    )

    with pytest.raises(
        CredentialInvalidDataError,
        match="Only draft credentials can be issued",
    ):
        service.complete_issuance(
            credential_id=draft_credential.id,
            signature="another-signature",
            key_id=KEY_ID,
        )


def test_get_issuer_signing_key_success(
    db_session,
    draft_credential,
    mocked_signing,
):
    service = CredentialService(db_session)

    key_id, public_key = service.get_issuer_signing_key(
        draft_credential.id
    )

    assert key_id == KEY_ID
    assert public_key == PUBLIC_KEY