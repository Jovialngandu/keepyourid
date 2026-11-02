
from uuid import UUID

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
