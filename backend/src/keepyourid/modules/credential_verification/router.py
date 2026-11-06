import logging
from collections import defaultdict, deque
from functools import lru_cache
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from keepyourid_verifier.engine import CredentialVerifier

from keepyourid.config import get_settings
from keepyourid.modules.credential_verification.schemas import (
    CredentialVerificationRequest,
    CredentialVerificationResponse,
)
from keepyourid.modules.credential_verification.service import (
    CredentialVerificationEngineError,
    CredentialVerificationService,
    CredentialVerificationValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/verifications",
    tags=["Credential Verification"],
)

VERIFICATION_RATE_LIMIT = 30
VERIFICATION_RATE_WINDOW_SECONDS = 60

_verification_hits: dict[str, deque[float]] = defaultdict(deque)


def verify_rate_limit(request: Request) -> None:
    client = request.client
    host = client.host if client else "unknown"

    now = monotonic()
    hits = _verification_hits[host]

    while hits and now - hits[0] > VERIFICATION_RATE_WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= VERIFICATION_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification requests.",
        )

    hits.append(now)


@lru_cache
def get_credential_verifier() -> CredentialVerifier:
    return CredentialVerifier()


def get_credential_verification_service() -> CredentialVerificationService:
    settings = get_settings()

    return CredentialVerificationService(
        verifier=get_credential_verifier(),
        allowed_status_list_hosts=settings.credential_status_list_allowed_hosts,
    )


@router.post(
    "",
    response_model=CredentialVerificationResponse,
)
def verify_credential(
    data: CredentialVerificationRequest,
    service: Annotated[
        CredentialVerificationService,
        Depends(get_credential_verification_service),
    ],
    _rate_limit: Annotated[None, Depends(verify_rate_limit)],
):
    try:
        return service.verify(data.signed_credential)

    except CredentialVerificationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except CredentialVerificationEngineError as exc:
        logger.exception("Credential verification engine failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credential verification failed.",
        ) from exc
