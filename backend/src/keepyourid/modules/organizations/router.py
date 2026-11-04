
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.core.auth import get_current_user
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
    OrganizationMembershipService,
    OrganizationService,
)
from keepyourid.modules.users.models import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def require_organization_access(
    user: User,
    organization_id: UUID,
    db: Session,
) -> None:
    membership = OrganizationMembershipService(db).ensure_user_access(
        user.id,
        organization_id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization.",
        )


@router.get("/", response_model=OrganizationListResponse)
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organizations = OrganizationService(db).list_by_user(current_user.id)
    return OrganizationListResponse(items=organizations)


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_organization_access(current_user, organization_id, db)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_organization_access(current_user, organization_id, db)

    dids = DIDService(db).list_by_organization(organization_id)
    return DIDListResponse(items=dids)


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return OrganizationService(db).register(
            data=data,
            owner_user=current_user,
        )
    except OrganizationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
