from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.core.dependencies import get_db
from keepyourid.modules.users.models import User, UserSession
from keepyourid.modules.users.service import UserService

SESSION_COOKIE_NAME = "keepyourid_session"


def get_token_from_request(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return token
    header = request.headers.get("authorization")
    if header and header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return None


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    token = get_token_from_request(request)
    if not token:
        return None
    user = UserService(db).get_current_user_from_token(token)
    if user is None:
        return None
    return user


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user = await get_current_user_optional(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user


def require_membership_for_organization(
    organization_id,
    db: Session,
    user: User,
) -> None:
    from keepyourid.modules.organizations.models import OrganizationMembership, MembershipStatus

    membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status == MembershipStatus.ACTIVE,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization.",
        )
