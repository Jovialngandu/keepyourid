from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from keepyourid.config import get_settings
from keepyourid.core.auth import SESSION_COOKIE_NAME, get_current_user, get_token_from_request
from keepyourid.core.dependencies import get_db
from keepyourid.modules.users.schemas import UserLoginRequest, UserRegisterRequest, UserResponse, UserSessionResponse
from keepyourid.modules.users.service import InvalidCredentialsError, UserAlreadyExistsError, UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _session_cookie_attrs() -> dict:
    settings = get_settings()
    samesite = settings.session_cookie_samesite
    secure = settings.session_cookie_secure
    if secure is None:
        secure = samesite.lower() == "none"
    return {
        "httponly": True,
        "samesite": samesite,
        "secure": secure,
        "path": "/",
    }


def _issue_session(db: Session, user, response: Response) -> UserSessionResponse:
    _, token = UserService(db).create_session(user)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=7 * 24 * 60 * 60,
        **_session_cookie_attrs(),
    )
    return UserSessionResponse(user=user, access_token=token)


@router.post("/register", response_model=UserSessionResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    data: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = UserService(db).register(data)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _issue_session(db, user, response)


@router.post("/login", response_model=UserSessionResponse)
def login_user(
    data: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = UserService(db).authenticate(data.email, data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return _issue_session(db, user, response)


@router.post("/logout")
def logout_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = get_token_from_request(request)
    UserService(db).logout(token)
    attrs = _session_cookie_attrs()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path=attrs["path"],
        samesite=attrs["samesite"],
        secure=attrs["secure"],
    )
    return {"success": True}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
