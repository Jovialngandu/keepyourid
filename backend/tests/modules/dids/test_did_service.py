
from uuid import uuid4

import pytest
from unittest.mock import MagicMock

from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.dids.schemas import DIDCreate, DIDProofSubmission
from keepyourid.modules.dids.service import (
    DIDAlreadyExistsError,
    DIDService,
    OrganizationNotFoundError,
)
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization


def create_organization(db_session):
    organization = Organization(
        legal_name="Test University",
        registration_number=f"ORG-{uuid4().hex[:8]}",
        email=f"{uuid4().hex[:8]}@example.com",
        status=OrganizationStatus.ACTIVE,
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    return organization


def test_register_did(db_session):
    organization = create_organization(db_session)
    service = DIDService(db_session)

    data = DIDCreate(
        identifier="did:ethr:sepolia:0x1234567890123456789012345678901234567890",
        method="ethr",
        document={
            "id": "did:ethr:sepolia:0x1234567890123456789012345678901234567890"
        },
    )

    result = service.register(organization.id, data)

    assert result.organization_id == organization.id
    assert result.identifier == data.identifier


def test_organization_can_only_have_one_did(db_session):
    organization = create_organization(db_session)
    service = DIDService(db_session)

    first = DIDCreate(
        identifier="did:example:university-1",
        method="example",
        document={"id": "did:example:university-1"},
    )

    second = DIDCreate(
        identifier="did:example:university-2",
        method="example",
        document={"id": "did:example:university-2"},
    )

    service.register(organization.id, first)

    with pytest.raises(DIDAlreadyExistsError):
        service.register(organization.id, second)


def test_register_did_for_unknown_organization(db_session):
    service = DIDService(db_session)

    data = DIDCreate(
        identifier="did:example:unknown",
        method="example",
        document={"id": "did:example:unknown"},
    )

    with pytest.raises(OrganizationNotFoundError):
        service.register(uuid4(), data)


def test_verify_control_registers_issuer_when_enabled(db_session, monkeypatch):
    organization = create_organization(db_session)
    did = DID(
        organization_id=organization.id,
        identifier="did:example:issuer-registration",
        method="example",
        document={"id": "did:example:issuer-registration"},
        status=DIDStatus.REGISTERED,
    )
    db_session.add(did)
    db_session.commit()
    db_session.refresh(did)

    challenge = MagicMock()
    challenge.id = uuid4()
    challenge.challenge = "challenge-value"
    challenge.purpose = "did_authentication"
    challenge.domain = "keepyourid.local"
    challenge.issued_at = None
    challenge.expires_at = None

    verifier = MagicMock()
    verifier.verify_authentication.return_value = {
        "verification_method": "#key-1",
        "signer_address": "0xabc",
    }

    issuer_service = MagicMock()
    issuer_service.register_issuer.return_value = {"status": "PENDING"}

    monkeypatch.setattr(
        "keepyourid.modules.dids.service.DIDChallengeService.validate_challenge",
        lambda self, *args, **kwargs: challenge,
    )
    monkeypatch.setattr(
        "keepyourid.modules.dids.service.DIDChallengeService.consume_challenge",
        lambda self, *args, **kwargs: None,
    )

    service = DIDService(db_session, issuer_registry_service=issuer_service)
    result = service.verify_control(
        did.id,
        DIDProofSubmission(
            challenge_id=challenge.id,
            verification_method="#key-1",
            signature="0xdeadbeef",
        ),
        verifier,
    )

    assert result["status"] == DIDStatus.VERIFIED.value
    issuer_service.register_issuer.assert_called_once_with(
        organization_id=organization.id,
        did_id=did.id,
        did=did.identifier,
        metadata={
            "organization_id": str(organization.id),
            "organization_name": organization.legal_name,
            "did_id": str(did.id),
        },
    )
