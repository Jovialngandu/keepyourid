from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from keepyourid.core.auth import SESSION_COOKIE_NAME, get_current_user
from keepyourid.core.dependencies import get_db
from keepyourid.modules.users.schemas import UserLoginRequest, UserRegisterRequest, UserResponse, UserSessionResponse
from keepyourid.modules.users.service import InvalidCredentialsError, UserAlreadyExistsError, UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(data: UserRegisterRequest, db: Session = Depends(get_db)):
    try:
        user = UserService(db).register(data)
        return user
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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

    _, token = UserService(db).create_session(user)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    return UserSessionResponse(user=user)


@router.post("/logout")
def logout_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    UserService(db).logout(token)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"success": True}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
