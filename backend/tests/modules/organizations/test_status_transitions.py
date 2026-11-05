
from uuid import uuid4

import pytest

from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization
from keepyourid.modules.organizations.service import (
    InvalidOrganizationTransitionError,
    OrganizationNotFoundError,
    OrganizationService,
)

from keepyourid.modules.users.models import User, UserStatus
from keepyourid.modules.organizations.schemas import OrganizationCreate

def create_organization(
    db_session,
    status=OrganizationStatus.SUSPENDED,
):
    organization = Organization(
        legal_name="Test Organization",
        registration_number=f"ORG-{uuid4().hex[:8]}",
        email=f"{uuid4().hex[:8]}@example.com",
        status=status,
    )

    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)

    return organization


def test_suspend_active_organization(db_session):
    organization = create_organization(
        db_session,
        status=OrganizationStatus.ACTIVE,
    )
    service = OrganizationService(db_session)

    result = service.suspend(organization.id)

    assert result.status == OrganizationStatus.SUSPENDED


def test_reactivate_suspended_organization(db_session):
    organization = create_organization(
        db_session,
        status=OrganizationStatus.SUSPENDED,
    )
    service = OrganizationService(db_session)

    result = service.reactivate(organization.id)

    assert result.status == OrganizationStatus.ACTIVE


def test_cannot_suspend_already_suspended_organization(db_session):
    organization = create_organization(db_session)
    service = OrganizationService(db_session)

    with pytest.raises(InvalidOrganizationTransitionError):
        service.suspend(organization.id)


def test_cannot_reactivate_active_organization(db_session):
    organization = create_organization(
        db_session,
        status=OrganizationStatus.ACTIVE,
    )
    service = OrganizationService(db_session)

    with pytest.raises(InvalidOrganizationTransitionError):
        service.reactivate(organization.id)


def test_register_organization_starts_active(db_session):
    owner = User(
        email="owner@example.com",
        full_name="Organization Owner",
        password_hash="test-password-hash",
        status=UserStatus.ACTIVE,
    )
    db_session.add(owner)
    db_session.flush()

    service = OrganizationService(db_session)

    result = service.register(
        data=OrganizationCreate(
            legal_name="Pending Org",
            registration_number="ORG-PENDING-001",
            email="pending@example.com",
            phone=None,
        ),
        owner_user=owner,
    )

    assert result.status == OrganizationStatus.ACTIVE
def test_organization_not_found(db_session):
    service = OrganizationService(db_session)

    with pytest.raises(OrganizationNotFoundError):
        service.suspend(uuid4())
