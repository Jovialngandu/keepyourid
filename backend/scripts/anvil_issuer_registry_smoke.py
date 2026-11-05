#!/usr/bin/env python3
"""Real DID -> IssuerRegistry smoke test on Anvil + PostgreSQL.

Required env vars:
  DATABASE_URL=postgresql+psycopg://keepyourid:keepyourid_dev@localhost:5434/keepyourid_db
  BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
  BLOCKCHAIN_CHAIN_ID=31337
  BLOCKCHAIN_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
  DID_RESOLVER_URL=unused_for_local_fake_resolver
  ISSUER_REGISTRY_ADDRESS=<deployed contract address>

If ISSUER_REGISTRY_ADDRESS is not set, the script will try to deploy the contract using
`forge script` and keep the address in the environment for the rest of the flow.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from eth_account import Account
from eth_account.messages import encode_defunct
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from keepyourid.blockchain.abi import load_issuer_registry_abi
from keepyourid.blockchain.adapters.ethereum_adapter import EthereumAdapter
from keepyourid.blockchain.config import BlockchainConfig
from keepyourid.blockchain.repositories.transaction_repository import (
    TransactionRepository,
)
from keepyourid.blockchain.services.issuer_registry_service import (
    IssuerRegistryService,
)
from keepyourid.blockchain.signers.local_signer import LocalAccountSigner
from keepyourid.core.database import Base
from keepyourid.modules.dids.challenge_service import DIDChallengeService
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.dids.schemas import DIDCreate, DIDProofSubmission
from keepyourid.modules.dids.service import DIDService
from keepyourid.verification.interfaces import ResolvedDID
from keepyourid.verification.did.service import DIDVerificationService
from keepyourid.verification.did.signature import (
    build_authentication_message,
)
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization
from keepyourid.modules.organizations.schemas import OrganizationCreate
from keepyourid.modules.organizations.service import OrganizationService


class FakeResolver:
    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document

    def resolve(self, did: str) -> ResolvedDID:
        return ResolvedDID(did=did, document=self.document, metadata={})


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def ensure_contract_deployed() -> str:
    registry_address = os.getenv("ISSUER_REGISTRY_ADDRESS")
    if registry_address:
        return registry_address

    rpc_url = require_env("BLOCKCHAIN_RPC_URL")
    private_key = require_env("BLOCKCHAIN_PRIVATE_KEY")

    cmd = [
        "forge",
        "script",
        "script/DeployIssuerRegistry.s.sol:DeployIssuerRegistry",
        "--rpc-url",
        rpc_url,
        "--private-key",
        private_key,
        "--broadcast",
        "--slow",
    ]

    result = subprocess.run(cmd, cwd="/home/dell/Documents/GitHub/keepyourid/backend/contracts", capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Deploy failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

    match = re.search(r"ISSUER_REGISTRY_ADDRESS=(0x[0-9a-fA-F]{40})", result.stdout)
    if not match:
        raise RuntimeError(f"Unable to detect deployed contract address from forge output:\n{result.stdout}")

    address = match.group(1)
    os.environ["ISSUER_REGISTRY_ADDRESS"] = address
    return address


def build_did_document(account: Account) -> tuple[str, str, dict[str, Any]]:
    did = f"did:ethr:sepolia:{account.address}"
    method_id = f"{did}#controller"
    document = {
        "id": did,
        "verificationMethod": [
            {
                "id": method_id,
                "type": "EcdsaSecp256k1RecoveryMethod2020",
                "controller": did,
                "blockchainAccountId": f"eip155:11155111:{account.address}",
            }
        ],
        "authentication": [method_id],
    }
    return did, method_id, document


def create_real_workflow() -> dict[str, Any]:
    database_url = require_env("DATABASE_URL")
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)

    session = Session(engine)
    try:
        org_service = OrganizationService(session)
        organization = org_service.register(
            OrganizationCreate(
                legal_name=f"Anvil Org {uuid4().hex[:6]}",
                registration_number=f"ORG-{uuid4().hex[:8]}",
                email=f"{uuid4().hex[:8]}@example.com",
                phone=None,
            )
        )
        org_service.approve(organization.id)

        private_key = require_env("BLOCKCHAIN_PRIVATE_KEY")
        did_private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(did_private_key)
        did, method_id, document = build_did_document(account)

        contract_address = ensure_contract_deployed()
        chain_id = int(require_env("BLOCKCHAIN_CHAIN_ID"))
        rpc_url = require_env("BLOCKCHAIN_RPC_URL")

        blockchain_config = BlockchainConfig(
            rpc_url=rpc_url,
            chain_id=chain_id,
            registry_address=contract_address,
            tx_timeout=120,
        )
        adapter = EthereumAdapter(blockchain_config, load_issuer_registry_abi())
        signer = LocalAccountSigner(private_key)
        repo = TransactionRepository(session)
        issuer_service = IssuerRegistryService(
            adapter=adapter,
            signer=signer,
            transaction_repository=repo,
            session=session,
        )

        did_service = DIDService(session, issuer_registry_service=issuer_service)
        created_did = did_service.register(
            organization.id,
            DIDCreate(
                identifier=did,
                method="ethr",
                document=document,
            ),
        )

        challenge_service = DIDChallengeService(session)
        challenge = challenge_service.create_challenge(
            created_did.id,
            purpose="did_authentication",
            domain="keepyourid.local",
        )

        message = build_authentication_message(
            did=did,
            challenge=challenge.challenge,
            purpose=challenge.purpose,
            domain=challenge.domain,
            issued_at=challenge.issued_at.isoformat(),
            expires_at=challenge.expires_at.isoformat(),
        )
        signature = "0x" + Account.sign_message(
            encode_defunct(text=message),
            private_key=account.key,
        ).signature.hex()

        proof = DIDProofSubmission(
            challenge_id=challenge.id,
            verification_method=method_id,
            signature=signature,
        )

        verifier = DIDVerificationService(resolver=FakeResolver(document))
        result = did_service.verify_control(
            created_did.id,
            proof,
            verifier,
        )

        transaction = repo.get_by_organization(organization.id)[0]
        tx_hash = transaction.transaction_hash
        receipt = adapter.get_transaction_receipt(tx_hash)
        issuer = issuer_service.get_issuer(did)

        if result.get("status") != DIDStatus.VERIFIED.value:
            raise RuntimeError(f"DID verification failed: {result}")
        if transaction.status != "CONFIRMED":
            raise RuntimeError(f"Blockchain transaction was not confirmed: {transaction.status}")
        if issuer is None or issuer.get("status") != "ACTIVE":
            raise RuntimeError(f"On-chain issuer not active after registration: {issuer}")
        if receipt is None or receipt.get("status") != 1:
            raise RuntimeError(f"Receipt absent or reverted: {receipt}")

        return {
            "organization_id": str(organization.id),
            "did_id": str(created_did.id),
            "did": did,
            "contract_address": contract_address,
            "transaction_hash": tx_hash,
            "transaction_status": transaction.status,
            "receipt_status": receipt["status"],
            "issuer_status": issuer["status"],
            "verified_status": result["status"],
            "chain_id": chain_id,
        }
    finally:
        session.close()


if __name__ == "__main__":
    try:
        result = create_real_workflow()
        print(json.dumps(result, indent=2, sort_keys=True))
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
