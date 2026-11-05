from datetime import datetime, timezone
from uuid import uuid4

from keepyourid.blockchain.enums import (
    BlockchainOperation,
    BlockchainTransactionStatus,
)
from keepyourid.blockchain.models import BlockchainTransaction
from keepyourid.modules.credentials.enums import CredentialStatus
from keepyourid.modules.credentials.schemas import CredentialCreate
from keepyourid.modules.credentials.service import CredentialService
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import (
    MembershipRole,
    MembershipStatus,
    Organization,
    OrganizationMembership,
)


def create_organization_with_owner(db_session, user, name):
    organization = Organization(
        legal_name=name,
        registration_number=f"ORG-{uuid4().hex[:8]}",
        email=f"{uuid4().hex[:8]}@example.com",
        status=OrganizationStatus.ACTIVE,
    )

    db_session.add(organization)
    db_session.flush()

    membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=user.id,
        role=MembershipRole.OWNER,
        status=MembershipStatus.ACTIVE,
    )

    db_session.add(membership)
    db_session.commit()
    db_session.refresh(organization)

    return organization


def create_verified_did(db_session, organization):
    identifier = f"did:ethr:sepolia:0x{uuid4().hex[:40]}"

    did = DID(
        organization_id=organization.id,
        identifier=identifier,
        method="ethr",
        document={
            "id": identifier,
            "verificationMethod": [],
            "authentication": [],
        },
        status=DIDStatus.VERIFIED,
    )

    db_session.add(did)
    db_session.commit()
    db_session.refresh(did)

    return did


def test_organization_detail_and_collection_routes(
    db_session,
    user,
    authenticated_client,
):
    organization = create_organization_with_owner(
        db_session,
        user,
        "Org Detail",
    )

    did = create_verified_did(db_session, organization)

    detail = authenticated_client.get(
        f"/api/v1/organizations/{organization.id}"
    )

    assert detail.status_code == 200
    assert detail.json()["id"] == str(organization.id)
    assert detail.json()["did"] == did.identifier

    listing = authenticated_client.get(
        "/api/v1/organizations/"
    )

    assert listing.status_code == 200
    assert any(
        item["id"] == str(organization.id)
        for item in listing.json()["items"]
    )


def test_did_detail_and_collection_routes(
    db_session,
    user,
    authenticated_client,
):
    organization = create_organization_with_owner(
        db_session,
        user,
        "Org DID",
    )

    did = create_verified_did(db_session, organization)

    detail = authenticated_client.get(
        f"/api/v1/dids/{did.id}"
    )

    assert detail.status_code == 200
    assert detail.json()["id"] == str(did.id)
    assert detail.json()["status"] == DIDStatus.VERIFIED.value

    listing = authenticated_client.get(
        f"/api/v1/organizations/{organization.id}/dids"
    )

    assert listing.status_code == 200
    assert any(
        item["id"] == str(did.id)
        for item in listing.json()["items"]
    )


def test_blockchain_transaction_routes_and_credential_revocation(
    db_session,
    user,
    authenticated_client,
):
    organization = create_organization_with_owner(
        db_session,
        user,
        "Org Tx",
    )

    did = create_verified_did(db_session, organization)

    tx = BlockchainTransaction(
        organization_id=organization.id,
        did_id=did.id,
        transaction_hash="0xabc123",
        chain_id=11155111,
        operation=BlockchainOperation.REGISTER_ISSUER,
        status=BlockchainTransactionStatus.PENDING.value,
        error_message=None,
    )

    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    service = CredentialService(db_session)

    credential = service.create_draft(
        organization.id,
        CredentialCreate(
            credential_type="UniversityDegreeCredential",
            subject={
                "id": "did:example:holder",
                "degree": "Computer Science",
            },
            valid_until=datetime(
                2030,
                1,
                1,
                tzinfo=timezone.utc,
            ),
        ),
    )

    credential.status = CredentialStatus.ISSUED

    db_session.add(credential)
    db_session.commit()
    db_session.refresh(credential)

    tx_list = authenticated_client.get(
        f"/api/v1/organizations/{organization.id}/transactions"
    )

    assert tx_list.status_code == 200
    assert any(
        item["id"] == str(tx.id)
        for item in tx_list.json()["items"]
    )

    tx_detail = authenticated_client.get(
        f"/api/v1/organizations/{organization.id}/transactions/{tx.id}"
    )

    assert tx_detail.status_code == 200
    assert tx_detail.json()["transaction_hash"] == tx.transaction_hash

    revoke = authenticated_client.post(
        f"/api/v1/organizations/{organization.id}/credentials/{credential.id}/revoke",
        json={"reason": "expired"},
    )

    assert revoke.status_code == 200
    assert revoke.json()["status"] == CredentialStatus.REVOKED.value