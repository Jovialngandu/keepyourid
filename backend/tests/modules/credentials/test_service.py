
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from keepyourid.modules.credentials.enums import CredentialStatus
from keepyourid.modules.credentials.schemas import CredentialCreate
from keepyourid.modules.credentials.service import (
    CredentialDIDNotFoundError,
    CredentialDIDNotVerifiedError,
    CredentialInvalidDataError,
    CredentialOrganizationInactiveError,
    CredentialOrganizationNotFoundError,
    CredentialService,
)
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization


@pytest.fixture
def active_organization(db_session):
    organization = Organization(
        legal_name="Test Organization",
        registration_number=f"REG-{uuid4()}",
        email=f"{uuid4()}@example.com",
        status=OrganizationStatus.ACTIVE,
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    return organization


@pytest.fixture
def verified_did(db_session, active_organization):
    did = DID(
        organization_id=active_organization.id,
        identifier=f"did:ethr:sepolia:0x{uuid4().hex[:40]}",
        method="ethr",
        document={},
        status=DIDStatus.VERIFIED,
    )
    db_session.add(did)
    db_session.commit()
    db_session.refresh(did)
    return did


@pytest.fixture
def credential_service(db_session):
    return CredentialService(db_session)


def valid_credential_data():
    return CredentialCreate(
        credential_type="AcademicCredential",
        subject={
            "name": "Test Subject",
            "degree": "Bachelor",
        },
    )


def test_create_draft_success(
    credential_service,
    active_organization,
    verified_did,
):
    credential = credential_service.create_draft(
        active_organization.id,
        valid_credential_data(),
    )

    assert credential.status == CredentialStatus.DRAFT
    assert credential.organization_id == active_organization.id
    assert credential.issuer_did_id == verified_did.id
    assert credential.credential_id.startswith("urn:uuid:")
    assert credential.proof is None

    assert credential.payload["issuer"] == verified_did.identifier
    assert credential.payload["type"] == [
        "VerifiableCredential",
        "AcademicCredential",
    ]
    assert credential.payload["credentialSubject"]["name"] == "Test Subject"


def test_create_draft_organization_not_found(credential_service):
    with pytest.raises(CredentialOrganizationNotFoundError):
        credential_service.create_draft(
            uuid4(),
            valid_credential_data(),
        )


def test_create_draft_organization_inactive(
    db_session,
    credential_service,
    active_organization,
):
    active_organization.status = OrganizationStatus.SUSPENDED
    db_session.commit()

    with pytest.raises(CredentialOrganizationInactiveError):
        credential_service.create_draft(
            active_organization.id,
            valid_credential_data(),
        )


def test_create_draft_without_did(
    credential_service,
    active_organization,
):
    with pytest.raises(CredentialDIDNotFoundError):
        credential_service.create_draft(
            active_organization.id,
            valid_credential_data(),
        )


def test_create_draft_with_unverified_did(
    db_session,
    credential_service,
    active_organization,
):
    did = DID(
        organization_id=active_organization.id,
        identifier=f"did:ethr:sepolia:0x{uuid4().hex[:40]}",
        method="ethr",
        document={},
        status=DIDStatus.REGISTERED,
    )
    db_session.add(did)
    db_session.commit()

    with pytest.raises(CredentialDIDNotVerifiedError):
        credential_service.create_draft(
            active_organization.id,
            valid_credential_data(),
        )


def test_create_draft_rejects_naive_expiration_date(
    credential_service,
    active_organization,
    verified_did,
):
    data = CredentialCreate.model_construct(
        credential_type="AcademicCredential",
        subject={"name": "Test Subject"},
        valid_until=datetime(2099, 1, 1),
    )

    with pytest.raises(CredentialInvalidDataError):
        credential_service.create_draft(
            active_organization.id,
            data,
        )


def test_get_created_credential(
    credential_service,
    active_organization,
    verified_did,
):
    created = credential_service.create_draft(
        active_organization.id,
        valid_credential_data(),
    )

    retrieved = credential_service.get(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id


def test_list_credentials_by_organization(
    credential_service,
    active_organization,
    verified_did,
):
    credential_service.create_draft(
        active_organization.id,
        valid_credential_data(),
    )

    credentials = credential_service.list_by_organization(
        active_organization.id,
    )

    assert len(credentials) == 1
    assert credentials[0].organization_id == active_organization.id
