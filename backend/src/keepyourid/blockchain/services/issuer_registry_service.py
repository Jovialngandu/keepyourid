import json
from enum import IntEnum
from typing import Any

from web3 import Web3

from keepyourid.blockchain.adapters.ethereum_adapter import EthereumAdapter
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
	) -> None:
		self.adapter = adapter
		self.signer = signer
  
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


	def register_issuer(
	self,
	did: str,
	metadata: dict[str, Any],
	) -> dict:
		did_hash = self.hash_did(did)
		metadata_hash = self.hash_metadata(metadata)

		if self.adapter.is_registered(did_hash):
			raise ValueError("Issuer already registered")

		return self.adapter.send_contract_transaction(
			self.adapter.contract.functions.registerIssuer(
				did_hash,
				metadata_hash,
			),
			self.signer,
		)


	def update_issuer_status(
		self,
		did: str,
		status: IssuerStatus,
	) -> dict:
		if status not in (IssuerStatus.ACTIVE, IssuerStatus.SUSPENDED):
			raise ValueError("Invalid issuer status")

		did_hash = self.hash_did(did)

		if not self.adapter.is_registered(did_hash):
			raise ValueError("Issuer not registered")

		return self.adapter.send_contract_transaction(
			self.adapter.contract.functions.updateIssuerStatus(
				did_hash,
				int(status),
			),
			self.signer,
		)
	
	def update_metadata(
		self,
		did: str,
		metadata: dict[str, Any],
	) -> dict:
		did_hash = self.hash_did(did)
		metadata_hash = self.hash_metadata(metadata)

		if not self.adapter.is_registered(did_hash):
			raise ValueError("Issuer not registered")

		return self.adapter.send_contract_transaction(
			self.adapter.contract.functions.updateMetadataHash(
				did_hash,
				metadata_hash,
			),
			self.signer,
		)