
from typing import Any, Protocol


class DIDMethodVerifier(Protocol):

    def validate_did_document(
        self,
        did: str,
        document: dict[str, Any],
    ) -> None:
        ...

    def get_authorized_method(
        self,
        did: str,
        document: dict[str, Any],
        verification_method: str,
    ) -> tuple[str, str]:
        ...