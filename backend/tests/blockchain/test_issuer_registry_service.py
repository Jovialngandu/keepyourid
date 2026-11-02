from unittest.mock import Mock

import pytest
from web3 import Web3

from keepyourid.blockchain.services.issuer_registry_service import (
    IssuerRegistryService,
    IssuerStatus,
)


@pytest.fixture
def adapter():
    return Mock()


@pytest.fixture
def signer():
    mock = Mock()
    mock.address = "0x1234567890123456789012345678901234567890"
    return mock


@pytest.fixture
def service(adapter, signer):
    return IssuerRegistryService(adapter, signer)


def test_hash_did(service):
    did = "did:ethr:sepolia:0x1234567890123456789012345678901234567890"

    result = service.hash_did(did)

    assert result == Web3.keccak(text=did)


def test_hash_metadata_is_deterministic(service):
    first = {"name": "Example", "country": "CD"}
    second = {"country": "CD", "name": "Example"}

    assert service.hash_metadata(first) == service.hash_metadata(second)


def test_register_issuer(service, adapter):
    adapter.is_registered.return_value = False
    adapter.send_contract_transaction.return_value = {
        "transaction_hash": "0xabc",
        "status": 1,
    }

    result = service.register_issuer(
        "did:ethr:sepolia:0x123",
        {"name": "Example"},
    )

    assert result["status"] == 1
    adapter.send_contract_transaction.assert_called_once()


def test_register_existing_issuer_fails(service, adapter):
    adapter.is_registered.return_value = True

    with pytest.raises(ValueError, match="already registered"):
        service.register_issuer(
            "did:ethr:sepolia:0x123",
            {"name": "Example"},
        )

    adapter.send_contract_transaction.assert_not_called()


def test_update_status(service, adapter):
    adapter.is_registered.return_value = True
    adapter.send_contract_transaction.return_value = {
        "transaction_hash": "0xdef",
        "status": 1,
    }

    result = service.update_issuer_status(
        "did:ethr:sepolia:0x123",
        IssuerStatus.SUSPENDED,
    )

    assert result["status"] == 1
    adapter.send_contract_transaction.assert_called_once()


def test_cannot_use_none_status(service):
    with pytest.raises(ValueError, match="Invalid issuer status"):
        service.update_issuer_status(
            "did:ethr:sepolia:0x123",
            IssuerStatus.NONE,
        )