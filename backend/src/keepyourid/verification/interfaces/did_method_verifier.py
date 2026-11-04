from typing import Any, Protocol


class DIDMethodVerifier(Protocol):
    def validate_did_document(
        self,
        did: str,
        document: dict[str, Any],
    ) -> None:
        ...