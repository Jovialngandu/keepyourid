
from src.keepyourid_verifier.checks.issuer import (
    extract_issuer_address,
    verify_issuer,
)


def test_extract_issuer_address():
    did = "did:ethr:sepolia:0xc72e7d6e5f9be7d93bfa1253cc70f5ad01d139ef"

    address = extract_issuer_address(did)

    assert address is not None
    assert address.lower() == (
        "0xc72e7d6e5f9be7d93bfa1253cc70f5ad01d139ef"
    )


def test_issuer_matches_signer():
    did = "did:ethr:sepolia:0xc72e7d6e5f9be7d93bfa1253cc70f5ad01d139ef"

    signer = "0xc72e7d6e5f9be7d93bfa1253cc70f5ad01d139ef"

    assert verify_issuer(did, signer)


def test_issuer_rejects_different_signer():
    did = "did:ethr:sepolia:0xc72e7d6e5f9be7d93bfa1253cc70f5ad01d139ef"

    signer = "0xcc90784875ffe61ad8cd135949f2734c3bea282d"

    assert not verify_issuer(did, signer)
