
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KeepYourID"
    app_env: str = "development"
    debug: bool = False
    database_url: str
    api_v1_prefix: str = "/api/v1"

    # Blockchain
    blockchain_rpc_url: str | None = None
    blockchain_chain_id: int | None = None
    issuer_registry_address: str | None = None
    blockchain_tx_timeout: int = 120
    blockchain_private_key: SecretStr | None = None

    # Credential verification
    credential_status_list_allowed_hosts: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
