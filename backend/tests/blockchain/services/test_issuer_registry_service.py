
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from web3.exceptions import TimeExhausted

from keepyourid.blockchain.enums import BlockchainOperation
from keepyourid.blockchain.services.issuer_registry_service import (
    IssuerRegistryService,
    IssuerStatus,
)


@pytest.fixture
def organization_id():
    return uuid4()


@pytest.fixture
def did_id():
    return uuid4()


@pytest.fixture
def did():
    return "did:ethr:sepolia:0x1234567890123456789012345678901234567890"


@pytest.fixture
def metadata():
    return {
        "name": "Test Organization",
        "type": "University",
    }


@pytest.fixture
def transaction():
    return SimpleNamespace(id=uuid4())


@pytest.fixture
def adapter():
    mock = MagicMock()
    mock.config.chain_id = 11155111
    mock.is_registered.return_value = False
    mock.is_active.return_value = True
    mock.get_issuer.return_value = {
        "did_hash": "0x1234",
        "metadata_hash": "0x5678",
        "status": 1,
        "registered_at": 100,
        "updated_at": 100,
    }
    mock.submit_contract_transaction.return_value = "0xtransaction123"
    mock.wait_for_transaction.return_value = {
        "transaction_hash": "0xtransaction123",
        "block_number": 100,
        "gas_used": 50000,
        "status": 1,
    }
    return mock


@pytest.fixture
def repository(transaction):
    mock = MagicMock()
    mock.create.return_value = transaction
    mock.get_by_id.return_value = transaction
    return mock


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def signer():
    return MagicMock()


@pytest.fixture
def contract():
    mock = MagicMock()
    mock.functions.registerIssuer.return_value = "register_function"
    mock.functions.updateIssuerStatus.return_value = "status_function"
    mock.functions.updateMetadataHash.return_value = "metadata_function"
    return mock


@pytest.fixture
def service(adapter, repository, session, signer, contract):
    adapter.contract = contract

    return IssuerRegistryService(
        adapter=adapter,
        signer=signer,
        transaction_repository=repository,
        session=session,
    )


# ---------------------------------------------------------
# Hashing
# ---------------------------------------------------------

def test_hash_did_returns_bytes(service, did):
    result = service.hash_did(did)

    assert isinstance(result, bytes)
    assert len(result) == 32


def test_hash_did_rejects_empty_value(service):
    with pytest.raises(ValueError, match="DID cannot be empty"):
        service.hash_did("")


def test_hash_metadata_returns_bytes(service, metadata):
    result = service.hash_metadata(metadata)

    assert isinstance(result, bytes)
    assert len(result) == 32


def test_hash_metadata_is_deterministic(service):
    first = service.hash_metadata({"name": "Test", "type": "University"})
    second = service.hash_metadata({"type": "University", "name": "Test"})

    assert first == second


# ---------------------------------------------------------
# Read operations
# ---------------------------------------------------------

def test_is_registered(service, adapter, did):
    adapter.is_registered.return_value = True

    assert service.is_registered(did) is True


def test_is_active(service, adapter, did):
    assert service.is_active(did) is True


def test_get_issuer_returns_none_when_not_registered(
    service,
    adapter,
    did,
):
    adapter.is_registered.return_value = False

    assert service.get_issuer(did) is None
    adapter.get_issuer.assert_not_called()


def test_get_issuer_returns_issuer_with_status_name(
    service,
    adapter,
    did,
):
    adapter.is_registered.return_value = True

    result = service.get_issuer(did)

    assert result is not None
    assert result["status"] == "ACTIVE"


# ---------------------------------------------------------
# Register issuer
# ---------------------------------------------------------

def test_register_issuer_rejects_existing_issuer(
    service,
    adapter,
    organization_id,
    did_id,
    did,
    metadata,
):
    adapter.is_registered.return_value = True

    with pytest.raises(ValueError, match="Issuer already registered"):
        service.register_issuer(
            organization_id,
            did_id,
            did,
            metadata,
        )

    service.transaction_repository.create.assert_not_called()


def test_register_issuer_creates_blockchain_transaction(
    service,
    adapter,
    repository,
    session,
    organization_id,
    did_id,
    did,
    metadata,
):
    result = service.register_issuer(
        organization_id,
        did_id,
        did,
        metadata,
    )

    repository.create.assert_called_once()

    kwargs = repository.create.call_args.kwargs

    assert kwargs["organization_id"] == organization_id
    assert kwargs["did_id"] == did_id
    assert kwargs["chain_id"] == 11155111
    assert kwargs["operation"] == BlockchainOperation.REGISTER_ISSUER

    adapter.submit_contract_transaction.assert_called_once()
    repository.mark_confirmed.assert_called_once()
    assert result["status"] == "CONFIRMED"
    assert session.commit.call_count >= 2


# ---------------------------------------------------------
# Update issuer status
# ---------------------------------------------------------

def test_update_status_rejects_invalid_status(
    service,
    organization_id,
    did_id,
    did,
):
    with pytest.raises(ValueError, match="Invalid issuer status"):
        service.update_issuer_status(
            organization_id,
            did_id,
            did,
            IssuerStatus.NONE,
        )


def test_update_status_rejects_unregistered_issuer(
    service,
    adapter,
    organization_id,
    did_id,
    did,
):
    adapter.is_registered.return_value = False

    with pytest.raises(ValueError, match="Issuer not registered"):
        service.update_issuer_status(
            organization_id,
            did_id,
            did,
            IssuerStatus.SUSPENDED,
        )




# ---------------------------------------------------------
# Update metadata
# ---------------------------------------------------------

def test_update_metadata_rejects_unregistered_issuer(
    service,
    adapter,
    organization_id,
    did_id,
    did,
    metadata,
):
    adapter.is_registered.return_value = False

    with pytest.raises(ValueError, match="Issuer not registered"):
        service.update_metadata(
            organization_id,
            did_id,
            did,
            metadata,
        )




# ---------------------------------------------------------
# Transaction outcomes
# ---------------------------------------------------------

def test_transaction_timeout_remains_pending(
    service,
    adapter,
    repository,
    organization_id,
    did_id,
    did,
    metadata,
):
    adapter.wait_for_transaction.side_effect = TimeExhausted(
        "Transaction not mined in time"
    )

    result = service.register_issuer(
        organization_id,
        did_id,
        did,
        metadata,
    )

    assert result["status"] == "PENDING"
    assert result["transaction_hash"] == "0xtransaction123"
    repository.mark_confirmed.assert_not_called()
    repository.mark_failed.assert_not_called()


def test_rpc_error_during_confirmation_remains_pending(
    service,
    adapter,
    repository,
    organization_id,
    did_id,
    did,
    metadata,
):
    adapter.wait_for_transaction.side_effect = ConnectionError(
        "RPC unavailable"
    )

    result = service.register_issuer(
        organization_id,
        did_id,
        did,
        metadata,
    )

    assert result["status"] == "PENDING"
    repository.mark_confirmed.assert_not_called()
    repository.mark_failed.assert_not_called()


def test_reverted_transaction_is_marked_failed(
    service,
    adapter,
    repository,
    organization_id,
    did_id,
    did,
    metadata,
):
    adapter.wait_for_transaction.return_value = {
        "transaction_hash": "0xtransaction123",
        "block_number": 100,
        "gas_used": 50000,
        "status": 0,
    }

    result = service.register_issuer(
        organization_id,
        did_id,
        did,
        metadata,
    )

    assert result["status"] == "FAILED"
    repository.mark_failed.assert_called_once()
    repository.mark_confirmed.assert_not_called()


def test_submission_error_keeps_transaction_pending(
    service,
    adapter,
    repository,
    organization_id,
    did_id,
    did,
    metadata,
):
    adapter.submit_contract_transaction.side_effect = ConnectionError(
        "RPC connection lost"
    )

    result = service.register_issuer(
        organization_id,
        did_id,
        did,
        metadata,
    )

    assert result["status"] == "PENDING"
    repository.mark_pending.assert_called_once()
    repository.mark_failed.assert_not_called()

def test_update_status_submits_operation(
    service,
    adapter,
    repository,
    organization_id,
    did_id,
    did,
):
    adapter.is_registered.return_value = True

    result = service.update_issuer_status(
        organization_id,
        did_id,
        did,
        IssuerStatus.SUSPENDED,
    )

    assert result["status"] == "CONFIRMED"

    kwargs = repository.create.call_args.kwargs
    assert kwargs["operation"] == BlockchainOperation.UPDATE_STATUS


def test_update_metadata_submits_operation(
    service,
    adapter,
    repository,
    organization_id,
    did_id,
    did,
    metadata,
):
    adapter.is_registered.return_value = True

    result = service.update_metadata(
        organization_id,
        did_id,
        did,
        metadata,
    )

    assert result["status"] == "CONFIRMED"

    kwargs = repository.create.call_args.kwargs
    assert kwargs["operation"] == BlockchainOperation.UPDATE_METADATA