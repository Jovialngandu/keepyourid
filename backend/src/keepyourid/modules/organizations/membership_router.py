from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.core.auth import get_current_user
from keepyourid.core.dependencies import get_db
from keepyourid.modules.organizations.models import (
    MembershipRole,
    MembershipStatus,
    Organization,
    OrganizationMembership,
)
from keepyourid.modules.organizations.service import OrganizationMembershipService
from keepyourid.modules.users.models import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _require_owner(user: User, organization_id: UUID, db: Session) -> None:
    membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status == MembershipStatus.ACTIVE,
        )
    )
    if membership is None or membership.role != MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the organization owner can manage members.",
        )


@router.get("/mine")
def get_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memberships = OrganizationMembershipService(db).list_for_user(current_user.id)
    if not memberships:
        return {"items": []}
    organization_ids = [membership.organization_id for membership in memberships]
    organizations = db.scalars(
        select(Organization).where(Organization.id.in_(organization_ids))
    ).all()
    return {"items": organizations}


@router.get("/{organization_id}/members")
def list_members(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = OrganizationMembershipService(db).ensure_user_access(
        current_user.id,
        organization_id,
    )
    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You do not belong to this organization.",
        )
    return {"items": OrganizationMembershipService(db).list_for_organization(organization_id)}


@router.post("/{organization_id}/members")
def add_member(
    organization_id: UUID,
    user_id: UUID,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(current_user, organization_id, db)
    membership = OrganizationMembershipService(db).add_member(organization_id, user_id, MembershipRole(role))
    return membership


@router.patch("/{organization_id}/members/{membership_id}")
def update_member(
    organization_id: UUID,
    membership_id: UUID,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(current_user, organization_id, db)
    membership = OrganizationMembershipService(db).get_membership(membership_id)
    if membership is None or membership.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Membership not found.")
    return OrganizationMembershipService(db).update_role(membership, MembershipRole(role))


@router.delete("/{organization_id}/members/{membership_id}")
def delete_member(
    organization_id: UUID,
    membership_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(current_user, organization_id, db)
    membership = OrganizationMembershipService(db).get_membership(membership_id)
    if membership is None or membership.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Membership not found.")
    OrganizationMembershipService(db).delete_membership(membership)
    return {"success": True}
