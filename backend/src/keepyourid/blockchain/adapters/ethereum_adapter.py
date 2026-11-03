
from web3 import Web3
from web3.contract import Contract

from keepyourid.blockchain.config import BlockchainConfig


class EthereumAdapter:
    def __init__(
        self,
        config: BlockchainConfig,
        abi: list[dict],
    ) -> None:
        self.config = config

        self.web3 = Web3(
            Web3.HTTPProvider(
                config.rpc_url,
                request_kwargs={"timeout": 30},
            )
        )

        if not self.web3.is_connected():
            raise ConnectionError("Unable to connect to Ethereum RPC")

        actual_chain_id = self.web3.eth.chain_id

        if actual_chain_id != config.chain_id:
            raise RuntimeError(
                f"Wrong network: expected {config.chain_id}, "
                f"got {actual_chain_id}"
            )

        address = Web3.to_checksum_address(config.registry_address)

        self.contract: Contract = self.web3.eth.contract(
            address=address,
            abi=abi,
        )

    @staticmethod
    def hash_did(did: str) -> bytes:
        if not did or not did.strip():
            raise ValueError("DID cannot be empty")

        return Web3.keccak(text=did)

    def is_registered(self, did_hash: bytes) -> bool:
        return self.contract.functions.isRegistered(did_hash).call()

    def is_active(self, did_hash: bytes) -> bool:
        return self.contract.functions.isActive(did_hash).call()

    def get_issuer(self, did_hash: bytes) -> dict:
        result = self.contract.functions.getIssuer(did_hash).call()

        return {
            "did_hash": result[0].hex(),
            "metadata_hash": result[1].hex(),
            "status": result[2],
            "registered_at": result[3],
            "updated_at": result[4],
        }

    def submit_contract_transaction(
        self,
        contract_function,
        signer,
    ) -> str:
        account_address = Web3.to_checksum_address(signer.address)

        nonce = self.web3.eth.get_transaction_count(
            account_address,
            "pending",
        )

        estimated_gas = contract_function.estimate_gas(
            {"from": account_address}
        )

        transaction = contract_function.build_transaction({
            "from": account_address,
            "nonce": nonce,
            "chainId": self.config.chain_id,
            "gas": int(estimated_gas * 1.2),
            "gasPrice": self.web3.eth.gas_price,
        })

        signed_transaction = signer.sign_transaction(transaction)

        tx_hash = self.web3.eth.send_raw_transaction(
            signed_transaction
        )

        return tx_hash.hex()

    def wait_for_transaction(self, tx_hash: str) -> dict:
        receipt = self.web3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=self.config.tx_timeout,
        )

        return {
            "transaction_hash": tx_hash,
            "block_number": receipt["blockNumber"],
            "status": receipt["status"],
            "gas_used": receipt["gasUsed"],
        }

    def get_transaction_receipt(self, tx_hash: str) -> dict | None:
        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        except Exception:
            return None

        return {
            "transaction_hash": tx_hash,
            "block_number": receipt["blockNumber"],
            "status": receipt["status"],
            "gas_used": receipt["gasUsed"],
        }

    @property
    def latest_block(self) -> int:
        return self.web3.eth.block_number
