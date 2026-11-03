from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.core.dependencies import get_db
from keepyourid.modules.dids.schemas import DIDListResponse
from keepyourid.modules.dids.service import DIDService
from keepyourid.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationListResponse,
    OrganizationResponse,
)
from keepyourid.modules.organizations.service import (
    OrganizationAlreadyExistsError,
    OrganizationService,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/", response_model=OrganizationListResponse)
def list_organizations(db: Session = Depends(get_db)):
    service = OrganizationService(db)
    return OrganizationListResponse(items=service.list())


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(organization_id: UUID, db: Session = Depends(get_db)):
    organization = OrganizationService(db).get(organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return organization


@router.get("/{organization_id}/dids", response_model=DIDListResponse)
def list_organization_dids(
    organization_id: UUID,
    db: Session = Depends(get_db),
):
    dids = DIDService(db).list_by_organization(organization_id)
    return DIDListResponse(items=dids)


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