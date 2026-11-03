from fastapi import FastAPI

from keepyourid.config import get_settings
from keepyourid.modules.health.router import router as health_router
from keepyourid.modules.organizations.router import router as organizations_router
from keepyourid.modules.dids.router import router as dids_router
from keepyourid.modules.credentials.router import router as credentials_router

from keepyourid.blockchain.abi import load_issuer_registry_abi
from keepyourid.blockchain.adapters.ethereum_adapter import EthereumAdapter
from keepyourid.blockchain.config import get_blockchain_config


def get_ethereum_adapter() -> EthereumAdapter:
    config = get_blockchain_config()
    abi = load_issuer_registry_abi()

    return EthereumAdapter(config, abi)




settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    organizations_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    dids_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    credentials_router,
    prefix=settings.api_v1_prefix,
)

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "message": "KeepYourID API",
        "docs": "/docs",
    }