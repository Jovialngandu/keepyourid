from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.core.dependencies import get_db
from keepyourid.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
)
from keepyourid.modules.organizations.service import (
    OrganizationAlreadyExistsError,
    OrganizationService,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
):
    service = OrganizationService(db)

    try:
        return service.register(data)
    except OrganizationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc