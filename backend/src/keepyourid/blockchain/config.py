
from dataclasses import dataclass

from keepyourid.config import get_settings


@dataclass(frozen=True)
class BlockchainConfig:
    rpc_url: str
    chain_id: int
    registry_address: str
    tx_timeout: int


def get_blockchain_config() -> BlockchainConfig:
    settings = get_settings()

    required = {
        "BLOCKCHAIN_RPC_URL": settings.blockchain_rpc_url,
        "BLOCKCHAIN_CHAIN_ID": settings.blockchain_chain_id,
        "ISSUER_REGISTRY_ADDRESS": settings.issuer_registry_address,
    }

    missing = [
        name for name, value in required.items()
        if value is None
    ]

    if missing:
        raise RuntimeError(
            f"Missing blockchain configuration: {', '.join(missing)}"
        )

    return BlockchainConfig(
        rpc_url=settings.blockchain_rpc_url,
        chain_id=settings.blockchain_chain_id,
        registry_address=settings.issuer_registry_address,
        tx_timeout=settings.blockchain_tx_timeout,
    )
