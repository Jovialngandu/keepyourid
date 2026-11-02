
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from keepyourid.modules.dids.challenge_models import DIDChallenge
from keepyourid.modules.dids.challenge_repository import DIDChallengeRepository
from keepyourid.modules.dids.models import DID


class DIDNotFoundError(Exception):
    pass


class DIDChallengeExpiredError(Exception):
    pass


class DIDChallengeAlreadyConsumedError(Exception):
    pass


class DIDChallengeService:
    CHALLENGE_TTL_MINUTES = 5

    def __init__(self, session: Session):
        self.session = session
        self.repository = DIDChallengeRepository(session)

    def create(self, did_id: UUID) -> DIDChallenge:
        did = self.session.get(DID, did_id)

        if did is None:
            raise DIDNotFoundError("DID not found.")

        challenge = DIDChallenge(
            did_id=did_id,
            challenge=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=self.CHALLENGE_TTL_MINUTES),
        )

        return self.repository.create(challenge)

    def validate_challenge(self, challenge_id: UUID) -> DIDChallenge:
        challenge = self.repository.get_by_id(challenge_id)

        if challenge is None:
            raise DIDNotFoundError("Challenge not found.")

        if challenge.consumed_at is not None:
            raise DIDChallengeAlreadyConsumedError(
                "Challenge has already been consumed."
            )

        if challenge.expires_at <= datetime.now(timezone.utc):
            raise DIDChallengeExpiredError("Challenge has expired.")

        return challenge
