from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from eth_account import Account
from eth_account.messages import encode_defunct

from keepyourid.verification.did.signature import (
    build_authentication_message,
)
from keepyourid.modules.holders.challenge_service import HolderDIDChallengeService
from keepyourid.modules.holders.service import HolderDIDService
from keepyourid.modules.users.models import User


@pytest.fixture
def user(db_session):
    user = User(
        email=f"holder-{uuid4()}@example.com",
        password_hash="hashed-password",
        full_name="Citizen Holder",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_holder_did_challenge_flow(db_session, user):
    service = HolderDIDService(db_session)
    account = Account.create()
    did_value = f"did:ethr:sepolia:{account.address}"
    method_id = f"{did_value}#controller"
    document = {
        "@context": ["https://w3id.org/did/v1"],
        "id": did_value,
        "verificationMethod": [
            {
                "id": method_id,
                "type": "EcdsaSecp256k1RecoveryMethod2020",
                "controller": did_value,
                "blockchainAccountId": f"eip155:11155111:{account.address}",
            }
        ],
        "authentication": [method_id],
    }

    did = service.register_user_did(
        user_id=user.id,
        identifier=did_value,
        method="ethr",
        document=document,
    )

    challenge = HolderDIDChallengeService(db_session).create_challenge(did.id)
    assert challenge.did_id == did.id

    message = build_authentication_message(
        did=did_value,
        challenge=challenge.challenge,
        purpose="did_authentication",
        domain="keepyourid.local",
        issued_at=challenge.issued_at.isoformat(),
        expires_at=challenge.expires_at.isoformat(),
    )
    signed = Account.sign_message(
        encode_defunct(text=message),
        private_key=account.key,
    )

    verified = service.verify_holder_did(
        did_id=did.id,
        challenge_id=challenge.id,
        signature=signed.signature.hex(),
        verification_method=method_id,
        purpose="did_authentication",
        domain="keepyourid.local",
        did_document=document,
    )

    assert verified["status"] == "VERIFIED"
    assert verified["holder_user_id"] == str(user.id)


def test_holder_credentials_are_filtered_by_user(db_session, user):
    service = HolderDIDService(db_session)
    account = Account.create()
    did_value = f"did:ethr:sepolia:{account.address}"
    did = service.register_user_did(
        user_id=user.id,
        identifier=did_value,
        method="ethr",
        document={
            "@context": ["https://w3id.org/did/v1"],
            "id": did_value,
            "verificationMethod": [
                {
                    "id": f"{did_value}#controller",
                    "type": "EcdsaSecp256k1RecoveryMethod2020",
                    "controller": did_value,
                    "blockchainAccountId": f"eip155:11155111:{account.address}",
                }
            ],
            "authentication": [f"{did_value}#controller"],
        },
    )

    credentials = service.list_user_credentials(user_id=user.id)
    assert credentials == []
    assert service.get_user_did(user_id=user.id, did_id=did.id).id == did.id
