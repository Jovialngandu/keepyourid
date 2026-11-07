import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from keepyourid.blockchain.abi import load_issuer_registry_abi
from keepyourid.blockchain.adapters.ethereum_adapter import EthereumAdapter
from keepyourid.blockchain.config import get_blockchain_config
from keepyourid.blockchain.router import router as blockchain_router
from keepyourid.config import get_settings
from keepyourid.modules.credential_verification.router import (
    router as credential_verification_router,
)
from keepyourid.modules.credentials.router import router as credentials_router
from keepyourid.modules.dids.router import router as dids_router
from keepyourid.modules.health.router import router as health_router
from keepyourid.modules.holders.router import router as holders_router
from keepyourid.modules.organizations.membership_router import (
    router as organization_membership_router,
)
from keepyourid.modules.organizations.router import router as organizations_router
from keepyourid.modules.users.router import router as users_router


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

allowed_origins = [
    item.strip()
    for item in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,https://keepyourid.vercel.app,https://keepyourid.onrender.com",
    ).split(",")
    if item.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    organization_membership_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    users_router,
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

app.include_router(
    credentials_router,
    # prefix=settings.api_v1_prefix,
)

app.include_router(
    credential_verification_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    holders_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    blockchain_router,
    prefix=settings.api_v1_prefix,
)

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "message": "KeepYourID API",
        "docs": "/docs",
        "kanda":"fort",
    }