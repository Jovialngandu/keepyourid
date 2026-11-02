from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from keepyourid.modules.dids.challenge_service import (
    DIDChallengeAlreadyConsumedError,
    DIDChallengeExpiredError,
    DIDChallengeService,
    DIDChallengeWrongContextError,
    DIDChallengeWrongDIDError,
    DIDNotFoundError,
)
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.models import Organization


def create_organization(db_session):
    organization = Organization(
        legal_name="Test Organization",
        registration_number=f"REG-{uuid4().hex[:12]}",
        email=f"{uuid4().hex[:12]}@example.com",
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    return organization


def create_did(db_session):
    organization = create_organization(db_session)

    did = DID(
        organization_id=organization.id,
        identifier=f"did:example:{uuid4().hex}",
        method="example",
        document={"id": f"did:example:{uuid4().hex}"},
    )

    db_session.add(did)
    db_session.commit()
    db_session.refresh(did)

    return did


def test_create_challenge(db_session):
    did = create_did(db_session)

    service = DIDChallengeService(db_session)
    challenge = service.create_challenge(
        did.id,
        purpose="did_authentication",
        domain="keepyourid.local",
    )

    assert challenge.id is not None
    assert challenge.did_id == did.id
    assert challenge.challenge
    assert len(challenge.challenge) > 20
    assert challenge.purpose == "did_authentication"
    assert challenge.domain == "keepyourid.local"
    assert challenge.issued_at is not None
    assert challenge.expires_at > datetime.now(timezone.utc)
    assert challenge.consumed_at is None


def test_create_challenge_for_nonexistent_did(db_session):
    service = DIDChallengeService(db_session)

    with pytest.raises(DIDNotFoundError):
        service.create_challenge(uuid4(), "did_authentication", "keepyourid.local")


def test_create_challenge_rejects_wrong_context(db_session):
    did = create_did(db_session)
    service = DIDChallengeService(db_session)

    with pytest.raises(DIDChallengeWrongContextError):
        service.create_challenge(did.id, "", "")


def test_consume_valid_challenge(db_session):
    did = create_did(db_session)
    service = DIDChallengeService(db_session)

    challenge = service.create_challenge(
        did.id,
        purpose="did_authentication",
        domain="keepyourid.local",
    )

    consumed = service.consume_challenge(
        challenge.id,
        did.id,
        purpose="did_authentication",
        domain="keepyourid.local",
    )

    assert consumed.consumed_at is not None
    assert consumed.id == challenge.id


def test_consume_challenge_with_wrong_did(db_session):
    did = create_did(db_session)
    other_did = create_did(db_session)
    service = DIDChallengeService(db_session)

    challenge = service.create_challenge(
        did.id,
        purpose="did_authentication",
        domain="keepyourid.local",
    )

    with pytest.raises(DIDChallengeWrongDIDError):
        service.consume_challenge(
            challenge.id,
            other_did.id,
            purpose="did_authentication",
            domain="keepyourid.local",
        )


def test_validate_nonexistent_challenge(db_session):
    service = DIDChallengeService(db_session)

    with pytest.raises(DIDNotFoundError):
        service.validate_challenge(uuid4())


def test_validate_expired_challenge(db_session):
    did = create_did(db_session)
    service = DIDChallengeService(db_session)

    challenge = service.create_challenge(
        did.id,
        purpose="did_authentication",
        domain="keepyourid.local",
    )

    challenge.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    with pytest.raises(DIDChallengeExpiredError):
        service.validate_challenge(challenge.id)


def test_validate_consumed_challenge(db_session):
    did = create_did(db_session)
    service = DIDChallengeService(db_session)

    challenge = service.create_challenge(
        did.id,
        purpose="did_authentication",
        domain="keepyourid.local",
    )

    challenge.consumed_at = datetime.now(timezone.utc)
    db_session.commit()

    with pytest.raises(DIDChallengeAlreadyConsumedError):
        service.validate_challenge(challenge.id)


def test_consume_challenge_twice_fails(db_session):
    did = create_did(db_session)
    service = DIDChallengeService(db_session)

    challenge = service.create_challenge(
        did.id,
        purpose="did_authentication",
        domain="keepyourid.local",
    )

    service.consume_challenge(
        challenge.id,
        did.id,
        purpose="did_authentication",
        domain="keepyourid.local",
    )

    with pytest.raises(DIDChallengeAlreadyConsumedError):
        service.consume_challenge(
            challenge.id,
            did.id,
            purpose="did_authentication",
            domain="keepyourid.local",
        )