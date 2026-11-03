
import json
from enum import IntEnum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from web3 import Web3
from web3.exceptions import TimeExhausted

from keepyourid.blockchain.adapters.ethereum_adapter import EthereumAdapter
from keepyourid.blockchain.enums import BlockchainOperation
from keepyourid.blockchain.repositories.transaction_repository import (
    TransactionRepository,
)
from keepyourid.blockchain.signers.transaction_signer import (
    TransactionSigner,
)


class IssuerStatus(IntEnum):
    NONE = 0
    ACTIVE = 1
    SUSPENDED = 2


class IssuerRegistryService:
    def __init__(
        self,
        adapter: EthereumAdapter,
        signer: TransactionSigner,
        transaction_repository: TransactionRepository,
        session: Session,
    ) -> None:
        self.adapter = adapter
        self.signer = signer
        self.transaction_repository = transaction_repository
        self.session = session

    @staticmethod
    def hash_did(did: str) -> bytes:
        if not did or not did.strip():
            raise ValueError("DID cannot be empty")

        return Web3.keccak(text=did)

    @staticmethod
    def hash_metadata(metadata: dict[str, Any]) -> bytes:
        canonical_metadata = json.dumps(
            metadata,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

        return Web3.keccak(text=canonical_metadata)

    def get_issuer(self, did: str) -> dict | None:
        did_hash = self.hash_did(did)

        if not self.adapter.is_registered(did_hash):
            return None

        issuer = self.adapter.get_issuer(did_hash)

        return {
            **issuer,
            "status": IssuerStatus(issuer["status"]).name,
        }

    def is_registered(self, did: str) -> bool:
        return self.adapter.is_registered(self.hash_did(did))

    def is_active(self, did: str) -> bool:
        return self.adapter.is_active(self.hash_did(did))

    def _execute_operation(
        self,
        organization_id: UUID,
        did_id: UUID,
        operation: BlockchainOperation,
        contract_function: Any,
    ) -> dict:
        transaction = self.transaction_repository.create(
            organization_id=organization_id,
            did_id=did_id,
            chain_id=self.adapter.config.chain_id,
            operation=operation,
        )

        transaction_id = str(transaction.id)

        # Persist the operation before contacting Ethereum.
        self.session.commit()

        try:
            tx_hash = self.adapter.submit_contract_transaction(
                contract_function,
                self.signer,
            )

            self.transaction_repository.set_transaction_hash(
                transaction,
                tx_hash,
            )
            self.session.commit()

        except Exception as exc:
            # The transaction may have been broadcast despite the RPC error.
            self.session.rollback()

            transaction = self.transaction_repository.get_by_id(
                UUID(transaction_id)
            )

            if transaction is not None:
                self.transaction_repository.mark_pending(
                    transaction,
                    str(exc),
                )
                self.session.commit()

            return {
                "transaction_id": transaction_id,
                "status": "PENDING",
                "error": "Submission outcome requires reconciliation",
            }

        try:
            receipt = self.adapter.wait_for_transaction(tx_hash)

        except TimeExhausted:
            return {
                "transaction_id": transaction_id,
                "transaction_hash": tx_hash,
                "status": "PENDING",
            }

        except Exception:
            # An RPC error does not prove that the transaction failed.
            return {
                "transaction_id": transaction_id,
                "transaction_hash": tx_hash,
                "status": "PENDING",
            }

        if receipt["status"] == 0:
            self.transaction_repository.mark_failed(
                transaction,
                "Transaction reverted on-chain",
            )
            self.session.commit()

            return {
                "transaction_id": transaction_id,
                **receipt,
                "status": "FAILED",
            }

        self.transaction_repository.mark_confirmed(
            transaction,
            block_number=receipt["block_number"],
            gas_used=receipt["gas_used"],
        )
        self.session.commit()

        return {
            "transaction_id": transaction_id,
            **receipt,
            "status": "CONFIRMED",
        }

    def register_issuer(
        self,
        organization_id: UUID,
        did_id: UUID,
        did: str,
        metadata: dict[str, Any],
    ) -> dict:
        did_hash = self.hash_did(did)
        metadata_hash = self.hash_metadata(metadata)

        if self.adapter.is_registered(did_hash):
            raise ValueError("Issuer already registered")

        contract_function = (
            self.adapter.contract.functions.registerIssuer(
                did_hash,
                metadata_hash,
            )
        )

        return self._execute_operation(
            organization_id,
            did_id,
            BlockchainOperation.REGISTER_ISSUER,
            contract_function,
        )

    def update_issuer_status(
        self,
        organization_id: UUID,
        did_id: UUID,
        did: str,
        status: IssuerStatus,
    ) -> dict:
        if status not in (
            IssuerStatus.ACTIVE,
            IssuerStatus.SUSPENDED,
        ):
            raise ValueError("Invalid issuer status")

        did_hash = self.hash_did(did)

        if not self.adapter.is_registered(did_hash):
            raise ValueError("Issuer not registered")

        contract_function = (
            self.adapter.contract.functions.updateIssuerStatus(
                did_hash,
                int(status),
            )
        )

        return self._execute_operation(
            organization_id,
            did_id,
            BlockchainOperation.UPDATE_STATUS,
            contract_function,
        )

    def update_metadata(
        self,
        organization_id: UUID,
        did_id: UUID,
        did: str,
        metadata: dict[str, Any],
    ) -> dict:
        did_hash = self.hash_did(did)
        metadata_hash = self.hash_metadata(metadata)

        if not self.adapter.is_registered(did_hash):
            raise ValueError("Issuer not registered")

        contract_function = (
            self.adapter.contract.functions.updateMetadataHash(
                did_hash,
                metadata_hash,
            )
        )

        return self._execute_operation(
            organization_id,
            did_id,
            BlockchainOperation.UPDATE_METADATA,
            contract_function,
        )
