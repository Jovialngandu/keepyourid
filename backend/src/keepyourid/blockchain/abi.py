import json
from pathlib import Path


def load_issuer_registry_abi() -> list[dict]:
    artifact_path = (
        Path(__file__).resolve().parents[4]
        / "contracts"
        / "out"
        / "IssuerRegistry.sol"
        / "IssuerRegistry.json"
    )

    if not artifact_path.exists():
        raise FileNotFoundError(
            f"IssuerRegistry artifact not found: {artifact_path}. "
            "Run forge build first."
        )

    with artifact_path.open(encoding="utf-8") as file:
        artifact = json.load(file)

    return artifact["abi"]