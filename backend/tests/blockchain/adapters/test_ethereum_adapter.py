
from unittest.mock import MagicMock, patch

import pytest
from web3 import Web3

from keepyourid.blockchain.adapters.ethereum_adapter import EthereumAdapter


@pytest.fixture
def config():
    return MagicMock(
        rpc_url="https://example-rpc.invalid",
        chain_id=11155111,
        registry_address="0x1234567890123456789012345678901234567890",
    )


@pytest.fixture
def web3_mock():
    mock = MagicMock()
    mock.is_connected.return_value = True
    mock.eth.chain_id = 11155111
    mock.eth.block_number = 12345
    return mock


@pytest.fixture
def adapter(config, web3_mock):
    with patch(
        "keepyourid.blockchain.adapters.ethereum_adapter.Web3"
    ) as web3_class:
        web3_class.HTTPProvider.return_value = MagicMock()
        web3_class.return_value = web3_mock
        web3_class.to_checksum_address.side_effect = (
            Web3.to_checksum_address
        )
        web3_class.keccak.side_effect = Web3.keccak

        yield EthereumAdapter(config, abi=[])

# ---------------------------------------------------------
# Initialization
# ---------------------------------------------------------

def test_adapter_initializes_successfully(adapter):
    assert adapter is not None


def test_adapter_rejects_unavailable_rpc(config):
    with patch(
        "keepyourid.blockchain.adapters.ethereum_adapter.Web3"
    ) as web3_class:
        web3_class.HTTPProvider.return_value = MagicMock()
        web3_class.return_value.is_connected.return_value = False

        with pytest.raises(ConnectionError):
            EthereumAdapter(config, abi=[])


def test_adapter_rejects_wrong_chain(config, web3_mock):
    web3_mock.eth.chain_id = 1

    with patch(
        "keepyourid.blockchain.adapters.ethereum_adapter.Web3"
    ) as web3_class:
        web3_class.HTTPProvider.return_value = MagicMock()
        web3_class.return_value = web3_mock
        web3_class.to_checksum_address.side_effect = lambda address: address

        with pytest.raises(RuntimeError):
            EthereumAdapter(config, abi=[])


# ---------------------------------------------------------
# DID hashing
# ---------------------------------------------------------

def test_hash_did_returns_keccak_hash(adapter):
    did = "did:ethr:sepolia:0x1234567890123456789012345678901234567890"

    assert adapter.hash_did(did) == Web3.keccak(text=did)


def test_hash_did_rejects_empty_value(adapter):
    with pytest.raises(ValueError):
        adapter.hash_did("")


# ---------------------------------------------------------
# Contract reads
# ---------------------------------------------------------

def test_is_registered(adapter):
    adapter.contract.functions.isRegistered.return_value.call.return_value = True

    result = adapter.is_registered(b"\x01" * 32)

    assert result is True


def test_is_active(adapter):
    adapter.contract.functions.isActive.return_value.call.return_value = True

    result = adapter.is_active(b"\x01" * 32)

    assert result is True


def test_get_issuer(adapter):
    adapter.contract.functions.getIssuer.return_value.call.return_value = (
        b"\x01" * 32,
        b"\x02" * 32,
        1,
        100,
        200,
    )

    result = adapter.get_issuer(b"\x01" * 32)

    assert result["status"] == 1
    assert result["registered_at"] == 100
    assert result["updated_at"] == 200


# ---------------------------------------------------------
# Transaction submission
# ---------------------------------------------------------

def test_submit_contract_transaction(adapter):
    contract_function = MagicMock()
    contract_function.build_transaction.return_value = {
        "nonce": 5,
        "chainId": 11155111,
        "gas": 100000,
        "gasPrice": 1000000000,
    }

    adapter.web3.eth.get_transaction_count.return_value = 5
    adapter.web3.eth.estimate_gas.return_value = 100000
    adapter.web3.eth.gas_price = 1000000000
    adapter.web3.eth.send_raw_transaction.return_value = bytes.fromhex(
        "ab" * 32
    )

    signer = MagicMock()
    signer.address = "0x1234567890123456789012345678901234567890"
    signer.sign_transaction.return_value = b"signed-transaction"

    result = adapter.submit_contract_transaction(
        contract_function,
        signer,
    )

    assert result == "ab" * 32
    signer.sign_transaction.assert_called_once()
    adapter.web3.eth.send_raw_transaction.assert_called_once()


# ---------------------------------------------------------
# Transaction receipts
# ---------------------------------------------------------

def test_wait_for_transaction_returns_receipt(adapter):
    adapter.web3.eth.wait_for_transaction_receipt.return_value = {
        "transactionHash": bytes.fromhex("ab" * 32),
        "blockNumber": 100,
        "gasUsed": 50000,
        "status": 1,
    }

    result = adapter.wait_for_transaction("0x" + "ab" * 32)

    assert result["status"] == 1
    assert result["block_number"] == 100
    assert result["gas_used"] == 50000


def test_wait_for_transaction_preserves_reverted_status(adapter):
    adapter.web3.eth.wait_for_transaction_receipt.return_value = {
        "transactionHash": bytes.fromhex("ab" * 32),
        "blockNumber": 100,
        "gasUsed": 50000,
        "status": 0,
    }

    result = adapter.wait_for_transaction("0x" + "ab" * 32)

    assert result["status"] == 0


def test_get_transaction_receipt_returns_none_when_unavailable(adapter):
    adapter.web3.eth.get_transaction_receipt.side_effect = Exception(
        "Transaction not found"
    )

    result = adapter.get_transaction_receipt("0x" + "ab" * 32)

    assert result is None


# ---------------------------------------------------------
# Blockchain state
# ---------------------------------------------------------

def test_latest_block(adapter):
    assert adapter.latest_block == 12345
