
from datetime import datetime, timedelta, timezone

import pytest
from eth_account import Account
from eth_account.messages import encode_defunct

from keepyourid.modules.dids.verification.interfaces import ResolvedDID
from keepyourid.modules.dids.verification.service import (
    DIDVerificationError,
    DIDVerificationService,
)
from keepyourid.modules.dids.verification.signature import (
    build_authentication_message,
)


class FakeResolver:
    def __init__(self, document):
        self.document = document

    def resolve(self, did):
        return ResolvedDID(
            did=did,
            document=self.document,
            metadata={},
        )


def create_test_identity():
    account = Account.create()

    did = f"did:ethr:sepolia:{account.address}"
    method_id = f"{did}#controller"

    document = {
        "id": did,
        "verificationMethod": [
            {
                "id": method_id,
                "type": "EcdsaSecp256k1RecoveryMethod2020",
                "controller": did,
                "blockchainAccountId": (
                    f"eip155:11155111:{account.address}"
                ),
            }
        ],
        "authentication": [method_id],
    }

    return account, did, method_id, document


def test_valid_did_authentication():
    account, did, method_id, document = create_test_identity()

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=5)

    challenge = "test-random-challenge"
    purpose = "did_authentication"
    domain = "keepyourid.local"

    message = build_authentication_message(
        did=did,
        challenge=challenge,
        purpose=purpose,
        domain=domain,
        issued_at=issued_at.isoformat(),
        expires_at=expires_at.isoformat(),
    )

    signed = Account.sign_message(
        encode_defunct(text=message),
        private_key=account.key,
    )

    service = DIDVerificationService(
        resolver=FakeResolver(document)
    )

    result = service.verify_authentication(
        did=did,
        challenge=challenge,
        purpose=purpose,
        domain=domain,
        issued_at=issued_at,
        expires_at=expires_at,
        verification_method=method_id,
        signature=signed.signature.hex(),
    )

    assert result["valid"] is True
    assert result["signer_address"].lower() == account.address.lower()
    assert result["verification_method"] == method_id


def test_reject_signature_from_wrong_key():
    account, did, method_id, document = create_test_identity()

    other_account = Account.create()

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=5)

    message = build_authentication_message(
        did=did,
        challenge="another-challenge",
        purpose="did_authentication",
        domain="keepyourid.local",
        issued_at=issued_at.isoformat(),
        expires_at=expires_at.isoformat(),
    )

    signed = Account.sign_message(
        encode_defunct(text=message),
        private_key=other_account.key,
    )

    service = DIDVerificationService(
        resolver=FakeResolver(document)
    )

    with pytest.raises(DIDVerificationError):
        service.verify_authentication(
            did=did,
            challenge="another-challenge",
            purpose="did_authentication",
            domain="keepyourid.local",
            issued_at=issued_at,
            expires_at=expires_at,
            verification_method=method_id,
            signature=signed.signature.hex(),
        )
