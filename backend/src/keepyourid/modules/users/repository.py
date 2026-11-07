from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.modules.users.models import User, UserSession


class UserRepository:
	def __init__(self, session: Session):
		self.session = session

	def create(self, user: User) -> User:
		self.session.add(user)
		self.session.commit()
		self.session.refresh(user)
		return user

	def get_by_email(self, email: str) -> User | None:
		return self.session.scalar(select(User).where(User.email == email))

	def get_by_id(self, user_id: UUID) -> User | None:
		return self.session.get(User, user_id)


class UserSessionRepository:
	def __init__(self, session: Session):
		self.session = session

	def create(self, session_record: UserSession) -> UserSession:
		self.session.add(session_record)
		self.session.commit()
		self.session.refresh(session_record)
		return session_record

	def get_by_token_hash(self, token_hash: str) -> UserSession | None:
		return self.session.scalar(
			select(UserSession).where(UserSession.token_hash == token_hash)
		)

	def revoke(self, session_record: UserSession) -> None:
		session_record.revoked_at = datetime.utcnow()
		self.session.commit()
