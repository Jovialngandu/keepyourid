from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from keepyourid.core.database import Base
from keepyourid.modules.organizations.models import Organization
from keepyourid.modules.organizations.enums import OrganizationStatus


def test_organization_creation(db_session):
    organization = Organization(
        legal_name="Université de Kinshasa",
        registration_number="ORG-001",
        email="contact@unikin.ac.cd",
    )

    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)

    assert isinstance(organization.id, UUID)
    assert organization.legal_name == "Université de Kinshasa"
    assert organization.status == OrganizationStatus.ACTIVE
    assert organization.created_at is not None
    assert organization.updated_at is not None


def test_organization_optional_fields(db_session):
    organization = Organization(
        legal_name="Test Organization",
        registration_number="ORG-002",
        email="test@example.com",
    )

    db_session.add(organization)
    db_session.commit()

    assert organization.phone is None
    assert organization.did is None


def test_organization_custom_status(db_session):
    organization = Organization(
        legal_name="Test Organization",
        registration_number="ORG-003",
        email="active@example.com",
        status=OrganizationStatus.ACTIVE,
    )

    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)

    assert organization.status == OrganizationStatus.ACTIVE