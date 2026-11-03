from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from keepyourid.blockchain.enums import (
    BlockchainOperation,
    BlockchainTransactionStatus,
)


class BlockchainTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    did_id: UUID
    transaction_hash: str | None
    chain_id: int
    operation: BlockchainOperation
    status: BlockchainTransactionStatus
    block_number: int | None
    gas_used: int | None
    error_message: str | None
    created_at: datetime
    confirmed_at: datetime | None


class BlockchainTransactionListResponse(BaseModel):
    items: list[BlockchainTransactionResponse]
