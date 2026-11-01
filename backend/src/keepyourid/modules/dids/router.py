
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
