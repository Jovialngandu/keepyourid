
from uuid import uuid4

import pytest

from keepyourid.modules.dids.schemas import DIDCreate
from keepyourid.modules.dids.service import (
    DIDAlreadyExistsError,
    DIDService,
    OrganizationNotFoundError,
)
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization


def create_organization(db_session):
    organization = Organization(
        legal_name="Test University",
        registration_number=f"ORG-{uuid4().hex[:8]}",
        email=f"{uuid4().hex[:8]}@example.com",
        status=OrganizationStatus.ACTIVE,
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    return organization


def test_register_did(db_session):
    organization = create_organization(db_session)
    service = DIDService(db_session)

    data = DIDCreate(
        identifier="did:ethr:sepolia:0x1234567890123456789012345678901234567890",
        method="ethr",
        document={
            "id": "did:ethr:sepolia:0x1234567890123456789012345678901234567890"
        },
    )

    result = service.register(organization.id, data)

    assert result.organization_id == organization.id
    assert result.identifier == data.identifier


def test_organization_can_only_have_one_did(db_session):
    organization = create_organization(db_session)
    service = DIDService(db_session)

    first = DIDCreate(
        identifier="did:example:university-1",
        method="example",
        document={"id": "did:example:university-1"},
    )

    second = DIDCreate(
        identifier="did:example:university-2",
        method="example",
        document={"id": "did:example:university-2"},
    )

    service.register(organization.id, first)

    with pytest.raises(DIDAlreadyExistsError):
        service.register(organization.id, second)


def test_register_did_for_unknown_organization(db_session):
    service = DIDService(db_session)

    data = DIDCreate(
        identifier="did:example:unknown",
        method="example",
        document={"id": "did:example:unknown"},
    )

    with pytest.raises(OrganizationNotFoundError):
        service.register(uuid4(), data)
