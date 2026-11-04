import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from keepyourid.modules.holders.models import HolderDID, HolderDIDChallenge


class HolderDIDNotFoundError(Exception):
    pass


class HolderDIDChallengeExpiredError(Exception):
    pass


class HolderDIDChallengeAlreadyConsumedError(Exception):
    pass


class HolderDIDChallengeWrongDIDError(Exception):
    pass


class HolderDIDChallengeWrongContextError(Exception):
    pass


class HolderDIDChallengeRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, challenge: HolderDIDChallenge) -> HolderDIDChallenge:
        self.session.add(challenge)
        self.session.commit()
        self.session.refresh(challenge)
        return challenge

    def get_by_id(self, challenge_id: UUID) -> HolderDIDChallenge | None:
        return self.session.get(HolderDIDChallenge, challenge_id)

    def consume(
        self,
        challenge_id: UUID,
        holder_did_id: UUID,
        purpose: str,
        domain: str,
    ) -> HolderDIDChallenge | None:
        now = datetime.now(timezone.utc)
        challenge = self.session.get(HolderDIDChallenge, challenge_id)
        if challenge is None:
            return None
        if challenge.holder_did_id != holder_did_id:
            return None
        if challenge.purpose != purpose or challenge.domain != domain:
            return None
        if challenge.consumed_at is not None or challenge.expires_at <= now:
            return None
        challenge.consumed_at = now
        self.session.commit()
        self.session.refresh(challenge)
        return challenge


class HolderDIDChallengeService:
    CHALLENGE_TTL_MINUTES = 5

    def __init__(self, session: Session):
        self.session = session
        self.repository = HolderDIDChallengeRepository(session)

    def _validate_context(self, purpose: str, domain: str) -> tuple[str, str]:
        normalized_purpose = (purpose or "").strip()
        normalized_domain = (domain or "").strip()
        if not normalized_purpose or not normalized_domain:
            raise HolderDIDChallengeWrongContextError(
                "Challenge purpose and domain are required."
            )
        return normalized_purpose, normalized_domain

    def create_challenge(
        self,
        holder_did_id: UUID | None = None,
        purpose: str = "did_authentication",
        domain: str = "keepyourid.local",
        did_id: UUID | None = None,
    ) -> HolderDIDChallenge:
        resolved_holder_did_id = holder_did_id or did_id
        if resolved_holder_did_id is None:
            raise HolderDIDNotFoundError("Holder DID not found.")

        did = self.session.get(HolderDID, resolved_holder_did_id)
        if did is None:
            raise HolderDIDNotFoundError("Holder DID not found.")

        normalized_purpose, normalized_domain = self._validate_context(purpose, domain)
        issued_at = datetime.now(timezone.utc)
        challenge = HolderDIDChallenge(
            holder_did_id=resolved_holder_did_id,
            challenge=secrets.token_urlsafe(32),
            purpose=normalized_purpose,
            domain=normalized_domain,
            issued_at=issued_at,
            expires_at=issued_at + timedelta(minutes=self.CHALLENGE_TTL_MINUTES),
        )
        return self.repository.create(challenge)

    def validate_challenge(
        self,
        challenge_id: UUID,
        holder_did_id: UUID | None = None,
        purpose: str | None = None,
        domain: str | None = None,
        did_id: UUID | None = None,
    ) -> HolderDIDChallenge:
        resolved_holder_did_id = holder_did_id or did_id
        challenge = self.repository.get_by_id(challenge_id)
        if challenge is None:
            raise HolderDIDNotFoundError("Challenge not found.")
        if resolved_holder_did_id is not None and challenge.holder_did_id != resolved_holder_did_id:
            raise HolderDIDChallengeWrongDIDError(
                "Challenge does not belong to this holder DID."
            )
        if purpose is not None and challenge.purpose != purpose.strip():
            raise HolderDIDChallengeWrongContextError(
                "Challenge purpose does not match the requested context."
            )
        if domain is not None and challenge.domain != domain.strip():
            raise HolderDIDChallengeWrongContextError(
                "Challenge domain does not match the requested context."
            )
        if challenge.consumed_at is not None:
            raise HolderDIDChallengeAlreadyConsumedError(
                "Challenge has already been consumed."
            )
        if challenge.expires_at <= datetime.now(timezone.utc):
            raise HolderDIDChallengeExpiredError("Challenge has expired.")
        return challenge

    def consume_challenge(
        self,
        challenge_id: UUID,
        holder_did_id: UUID | None = None,
        purpose: str = "did_authentication",
        domain: str = "keepyourid.local",
        did_id: UUID | None = None,
    ) -> HolderDIDChallenge:
        resolved_holder_did_id = holder_did_id or did_id
        if resolved_holder_did_id is None:
            raise HolderDIDNotFoundError("Holder DID not found.")
        normalized_purpose, normalized_domain = self._validate_context(purpose, domain)
        challenge = self.validate_challenge(
            challenge_id,
            holder_did_id=resolved_holder_did_id,
            purpose=normalized_purpose,
            domain=normalized_domain,
        )
        consumed = self.repository.consume(
            challenge_id=challenge.id,
            holder_did_id=resolved_holder_did_id,
            purpose=normalized_purpose,
            domain=normalized_domain,
        )
        if consumed is None:
            raise HolderDIDChallengeWrongContextError(
                "Challenge cannot be consumed with the provided context."
            )
        return consumed
