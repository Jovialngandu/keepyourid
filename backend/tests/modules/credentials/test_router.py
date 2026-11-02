
from uuid import uuid4

from fastapi.testclient import TestClient

from keepyourid.main import app
from keepyourid.core.dependencies import get_db
from keepyourid.modules.credentials.enums import CredentialStatus
from keepyourid.modules.credentials.models import VerifiableCredential
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization


def create_organization(db_session):
    organization = Organization(
        legal_name="Router Test Organization",
        registration_number=f"REG-{uuid4()}",
        email=f"{uuid4()}@example.com",
        status=OrganizationStatus.ACTIVE,
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    return organization


def create_verified_did(db_session, organization):
    did = DID(
        organization_id=organization.id,
        identifier=f"did:ethr:sepolia:0x{uuid4().hex[:40]}",
        method="ethr",
        document={},
        status=DIDStatus.VERIFIED,
    )
    db_session.add(did)
    db_session.commit()
    db_session.refresh(did)
    return did


def test_create_credential_endpoint(db_session):
    organization = create_organization(db_session)
    create_verified_did(db_session, organization)

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/organizations/{organization.id}/credentials",
                json={
                    "credential_type": "AcademicCredential",
                    "subject": {
                        "name": "Test Subject",
                        "degree": "Bachelor",
                    },
                },
            )

        assert response.status_code == 201
        assert response.json()["status"] == CredentialStatus.DRAFT.value
        assert response.json()["credential_type"] == "AcademicCredential"
    finally:
        app.dependency_overrides.clear()


def test_list_credentials_endpoint(db_session):
    organization = create_organization(db_session)
    did = create_verified_did(db_session, organization)

    credential = VerifiableCredential(
        credential_id=f"urn:uuid:{uuid4()}",
        organization_id=organization.id,
        issuer_did_id=did.id,
        credential_type="AcademicCredential",
        credential_subject={"name": "Test Subject"},
        payload={
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["VerifiableCredential", "AcademicCredential"],
            "issuer": did.identifier,
            "credentialSubject": {"name": "Test Subject"},
        },
        proof=None,
        status=CredentialStatus.DRAFT,
        valid_from=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    )
    db_session.add(credential)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/v1/organizations/{organization.id}/credentials"
            )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["credential_id"] == credential.credential_id
    finally:
        app.dependency_overrides.clear()


def test_get_credential_from_another_organization_returns_404(db_session):
    organization_a = create_organization(db_session)
    organization_b = create_organization(db_session)
    did_a = create_verified_did(db_session, organization_a)

    credential = VerifiableCredential(
        credential_id=f"urn:uuid:{uuid4()}",
        organization_id=organization_a.id,
        issuer_did_id=did_a.id,
        credential_type="AcademicCredential",
        credential_subject={"name": "Test Subject"},
        payload={"issuer": did_a.identifier},
        proof=None,
        status=CredentialStatus.DRAFT,
        valid_from=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    )
    db_session.add(credential)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/v1/organizations/{organization_b.id}"
                f"/credentials/{credential.id}"
            )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
