
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from keepyourid.modules.dids.challenge_models import DIDChallenge


class DIDChallengeRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, challenge_id: UUID) -> DIDChallenge | None:
        return self.session.get(DIDChallenge, challenge_id)

    def create(self, challenge: DIDChallenge) -> DIDChallenge:
        self.session.add(challenge)
        self.session.commit()
        self.session.refresh(challenge)
        return challenge

    def consume(
        self,
        challenge_id: UUID,
        did_id: UUID,
        purpose: str,
        domain: str,
    ) -> DIDChallenge | None:
        stmt = (
            update(DIDChallenge)
            .where(DIDChallenge.id == challenge_id)
            .where(DIDChallenge.did_id == did_id)
            .where(DIDChallenge.purpose == purpose)
            .where(DIDChallenge.domain == domain)
            .where(DIDChallenge.consumed_at.is_(None))
            .where(DIDChallenge.expires_at > datetime.now(timezone.utc))
            .values(consumed_at=datetime.now(timezone.utc))
        )

        self.session.execute(stmt)
        self.session.commit()

        return self.session.get(DIDChallenge, challenge_id)
