from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.core.security import generate_token, hash_password, hash_token, verify_password
from keepyourid.modules.users.models import User, UserSession, UserStatus
from keepyourid.modules.users.repository import UserRepository, UserSessionRepository
from keepyourid.modules.users.schemas import UserRegisterRequest


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = UserRepository(session)
        self.session_repository = UserSessionRepository(session)

    def register(self, data: UserRegisterRequest) -> User:
        normalized_email = str(data.email).strip().lower()
        if self.repository.get_by_email(normalized_email):
            raise UserAlreadyExistsError("A user with this email already exists.")

        user = User(
            email=normalized_email,
            full_name=data.full_name.strip(),
            password_hash=hash_password(data.password),
            status=UserStatus.ACTIVE,
        )
        return self.repository.create(user)

    def authenticate(self, email: str, password: str) -> User:
        user = self.repository.get_by_email(str(email).strip().lower())
        if user is None or user.status != UserStatus.ACTIVE:
            raise InvalidCredentialsError("Invalid email or password.")
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")
        return user

    def create_session(self, user: User) -> tuple[UserSession, str]:
        token = generate_token()
        session_record = UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked_at=None,
        )
        created = self.session_repository.create(session_record)
        return created, token

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.repository.get_by_id(user_id)

    def get_current_user_from_token(self, token: str | None) -> User | None:
        if not token:
            return None
        session_record = self.session_repository.get_by_token_hash(hash_token(token))
        if session_record is None:
            return None
        if session_record.revoked_at is not None or session_record.expires_at <= datetime.now(timezone.utc):
            return None
        user = self.repository.get_by_id(session_record.user_id)
        if user is None or user.status != UserStatus.ACTIVE:
            return None
        return user

    def logout(self, token: str | None) -> None:
        if not token:
            return
        session_record = self.session_repository.get_by_token_hash(hash_token(token))
        if session_record is not None:
            self.session_repository.revoke(session_record)

    def list_by_ids(self, user_ids: list[UUID]) -> list[User]:
        if not user_ids:
            return []
        statement = select(User).where(User.id.in_(user_ids))
        return list(self.session.scalars(statement).all())
