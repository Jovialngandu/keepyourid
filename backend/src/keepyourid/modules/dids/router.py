
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.core.dependencies import get_db
from keepyourid.modules.dids.schemas import DIDCreate, DIDResponse
from keepyourid.modules.dids.service import (
    DIDAlreadyExistsError,
    DIDService,
    OrganizationInactiveError,
    OrganizationNotFoundError,
)

from keepyourid.modules.dids.challenge_service import (
    DIDChallengeAlreadyConsumedError,
    DIDChallengeExpiredError,
    DIDChallengeService,
    DIDChallengeWrongContextError,
    DIDChallengeWrongDIDError,
    DIDNotFoundError,
)
from keepyourid.modules.dids.schemas import (
    DIDChallengeConsume,
    DIDChallengeCreate,
    DIDChallengeResponse,
)


router = APIRouter(prefix="/dids", tags=["DIDs"])


@router.post(
    "/organizations/{organization_id}",
    response_model=DIDResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_did(
    organization_id: UUID,
    data: DIDCreate,
    db: Session = Depends(get_db),
):
    service = DIDService(db)

    try:
        return service.register(organization_id, data)

    except OrganizationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except OrganizationInactiveError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except DIDAlreadyExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/{did_id}/challenges",
    response_model=DIDChallengeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_did_challenge(
    did_id: UUID,
    data: DIDChallengeCreate,
    db: Session = Depends(get_db),
):
    try:
        challenge = DIDChallengeService(db).create_challenge(
            did_id,
            purpose=data.purpose,
            domain=data.domain,
        )

        return DIDChallengeResponse(
            challenge_id=challenge.id,
            challenge=challenge.challenge,
            purpose=challenge.purpose,
            domain=challenge.domain,
            issued_at=challenge.issued_at,
            expires_at=challenge.expires_at,
        )

    except DIDNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DIDChallengeWrongContextError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/{did_id}/challenges/{challenge_id}/consume",
    response_model=DIDChallengeResponse,
    status_code=status.HTTP_200_OK,
)
def consume_did_challenge(
    did_id: UUID,
    challenge_id: UUID,
    data: DIDChallengeConsume,
    db: Session = Depends(get_db),
):
    try:
        challenge = DIDChallengeService(db).consume_challenge(
            challenge_id,
            did_id,
            purpose=data.purpose,
            domain=data.domain,
        )

        return DIDChallengeResponse(
            challenge_id=challenge.id,
            challenge=challenge.challenge,
            purpose=challenge.purpose,
            domain=challenge.domain,
            issued_at=challenge.issued_at,
            expires_at=challenge.expires_at,
        )

    except DIDNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DIDChallengeWrongDIDError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DIDChallengeWrongContextError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DIDChallengeAlreadyConsumedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DIDChallengeExpiredError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
