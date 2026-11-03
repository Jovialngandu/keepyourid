from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.blockchain.enums import (
	BlockchainOperation,
	BlockchainTransactionStatus,
)
from keepyourid.blockchain.models import BlockchainTransaction


class TransactionRepository:
	def __init__(self, session: Session) -> None:
		self.session = session

	def create(
		self,
		organization_id: UUID,
		did_id: UUID,
		chain_id: int,
		operation: BlockchainOperation,
		transaction_hash: str | None = None,
	) -> BlockchainTransaction:

		transaction = BlockchainTransaction(
			organization_id=organization_id,
			did_id=did_id,
			chain_id=chain_id,
			operation=operation.value,
			transaction_hash=transaction_hash,
			status=BlockchainTransactionStatus.PENDING.value,
		)

		self.session.add(transaction)
		self.session.flush()

		return transaction

	def mark_confirmed(
		self,
		transaction: BlockchainTransaction,
		block_number: int,
		gas_used: int,
	) -> BlockchainTransaction:

		transaction.status = BlockchainTransactionStatus.CONFIRMED.value
		transaction.block_number = block_number
		transaction.gas_used = gas_used
		transaction.confirmed_at = datetime.now(timezone.utc)

		self.session.flush()

		return transaction

	def mark_failed(
		self,
		transaction: BlockchainTransaction,
		error_message: str,
	) -> BlockchainTransaction:
		transaction.status = BlockchainTransactionStatus.FAILED
		transaction.error_message = error_message[:2000]
		self.session.flush()
		return transaction

	def get_by_hash(
		self,
		chain_id: int,
		transaction_hash: str,
	) -> BlockchainTransaction | None:

		statement = select(BlockchainTransaction).where(
			BlockchainTransaction.chain_id == chain_id,
			BlockchainTransaction.transaction_hash == transaction_hash,
		)

		return self.session.scalar(statement)

	def get_by_organization(
		self,
		organization_id: UUID,
	) -> list[BlockchainTransaction]:

		statement = (
			select(BlockchainTransaction)
			.where(
				BlockchainTransaction.organization_id == organization_id
			)
			.order_by(BlockchainTransaction.created_at.desc())
		)

		return list(self.session.scalars(statement).all())
	
	def set_transaction_hash(
	self,
	transaction: BlockchainTransaction,
	transaction_hash: str,
	) -> BlockchainTransaction:
		transaction.transaction_hash = transaction_hash
		self.session.flush()
		return transaction


	def mark_pending(
		self,
		transaction: BlockchainTransaction,
		error_message: str | None = None,
	) -> BlockchainTransaction:
		transaction.status = BlockchainTransactionStatus.PENDING
		transaction.error_message = error_message
		self.session.flush()
		return transaction

	def get_by_id(
	self,
	transaction_id: UUID,
	) -> BlockchainTransaction | None:
		return self.session.get(
			BlockchainTransaction,
			transaction_id,
		)