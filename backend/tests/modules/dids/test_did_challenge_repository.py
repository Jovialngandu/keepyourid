from uuid import uuid4

from keepyourid.modules.dids.challenge_models import DIDChallenge
from keepyourid.modules.dids.challenge_repository import DIDChallengeRepository
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.models import Organization


def test_create_and_get_challenge(db_session):
    organization = Organization(
        legal_name="Repository Test",
        registration_number=f"REG-{uuid4().hex[:12]}",
        email=f"{uuid4().hex[:12]}@example.com",
    )
    db_session.add(organization)
    db_session.commit()

    did = DID(
        organization_id=organization.id,
        identifier=f"did:example:{uuid4().hex}",
        method="example",
        document={"id": "test"},
    )
    db_session.add(did)
    db_session.commit()

    challenge = DIDChallenge(
        did_id=did.id,
        challenge=f"challenge-{uuid4().hex}",
        expires_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    )

    repository = DIDChallengeRepository(db_session)
    created = repository.create(challenge)

    retrieved = repository.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.did_id == did.id