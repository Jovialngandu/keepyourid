import json
from importlib.resources import files


def load_issuer_registry_abi() -> list[dict]:
    artifact_path = (
        files("keepyourid.blockchain")
        .joinpath("artifacts/IssuerRegistry.json")
    )

    artifact = json.loads(
        artifact_path.read_text(encoding="utf-8")
    )

    return artifact["abi"]