from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.blockchain.repositories.transaction_repository import TransactionRepository
from keepyourid.blockchain.schemas import (
    BlockchainTransactionListResponse,
    BlockchainTransactionResponse,
)
from keepyourid.core.dependencies import get_db

router = APIRouter(prefix="/organizations/{organization_id}", tags=["Blockchain"])


@router.get("/transactions", response_model=BlockchainTransactionListResponse)
def list_organization_transactions(
    organization_id: UUID,
    db: Session = Depends(get_db),
):
    transactions = TransactionRepository(db).get_by_organization(organization_id)
    return BlockchainTransactionListResponse(items=transactions)


@router.get("/transactions/{transaction_id}", response_model=BlockchainTransactionResponse)
def get_organization_transaction(
    organization_id: UUID,
    transaction_id: UUID,
    db: Session = Depends(get_db),
):
    transaction = TransactionRepository(db).get_by_id(transaction_id)
    if transaction is None or transaction.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )
    return transaction
