
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


class DIDChallengeWrongDIDError(Exception):
    pass


class DIDChallengeWrongContextError(Exception):
    pass


class DIDChallengeService:
    CHALLENGE_TTL_MINUTES = 5

    def __init__(self, session: Session):
        self.session = session
        self.repository = DIDChallengeRepository(session)

    def _validate_context(self, purpose: str, domain: str) -> tuple[str, str]:
        normalized_purpose = (purpose or "").strip()
        normalized_domain = (domain or "").strip()

        if not normalized_purpose or not normalized_domain:
            raise DIDChallengeWrongContextError(
                "Challenge purpose and domain are required."
            )

        return normalized_purpose, normalized_domain

    def create_challenge(
        self,
        did_id: UUID,
        purpose: str,
        domain: str,
    ) -> DIDChallenge:
        did = self.session.get(DID, did_id)
        if did is None:
            raise DIDNotFoundError("DID not found.")

        normalized_purpose, normalized_domain = self._validate_context(
            purpose,
            domain,
        )

        issued_at = datetime.now(timezone.utc)
        challenge = DIDChallenge(
            did_id=did_id,
            challenge=secrets.token_urlsafe(32),
            purpose=normalized_purpose,
            domain=normalized_domain,
            issued_at=issued_at,
            expires_at=issued_at + timedelta(minutes=self.CHALLENGE_TTL_MINUTES),
        )

        return self.repository.create(challenge)

    def create(self, did_id: UUID) -> DIDChallenge:
        return self.create_challenge(did_id, "did_authentication", "keepyourid.local")

    def validate_challenge(
        self,
        challenge_id: UUID,
        did_id: UUID | None = None,
        purpose: str | None = None,
        domain: str | None = None,
    ) -> DIDChallenge:
        challenge = self.repository.get_by_id(challenge_id)

        if challenge is None:
            raise DIDNotFoundError("Challenge not found.")

        if did_id is not None and challenge.did_id != did_id:
            raise DIDChallengeWrongDIDError("Challenge does not belong to this DID.")

        if purpose is not None and challenge.purpose != purpose.strip():
            raise DIDChallengeWrongContextError(
                "Challenge purpose does not match the requested context."
            )

        if domain is not None and challenge.domain != domain.strip():
            raise DIDChallengeWrongContextError(
                "Challenge domain does not match the requested context."
            )

        if challenge.consumed_at is not None:
            raise DIDChallengeAlreadyConsumedError(
                "Challenge has already been consumed."
            )

        if challenge.expires_at <= datetime.now(timezone.utc):
            raise DIDChallengeExpiredError("Challenge has expired.")

        return challenge


    def consume_challenge(
        self,
        challenge_id: UUID,
        did_id: UUID,
        purpose: str,
        domain: str,
    ) -> DIDChallenge:
        normalized_purpose, normalized_domain = self._validate_context(
            purpose,
            domain,
        )

        self.validate_challenge(
            challenge_id,
            did_id=did_id,
            purpose=normalized_purpose,
            domain=normalized_domain,
        )

        consumed = self.repository.consume(
            challenge_id,
            did_id,
            normalized_purpose,
            normalized_domain,
        )

        if consumed is None:
            refreshed = self.repository.get_by_id(challenge_id)

            if refreshed is None:
                raise DIDNotFoundError("Challenge not found.")

            if refreshed.consumed_at is not None:
                raise DIDChallengeAlreadyConsumedError(
                    "Challenge has already been consumed."
                )

            if refreshed.expires_at <= datetime.now(timezone.utc):
                raise DIDChallengeExpiredError("Challenge has expired.")

            raise DIDChallengeWrongContextError(
                "Challenge cannot be consumed with the provided context."
            )

        return consumed

