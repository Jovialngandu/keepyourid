from urllib.parse import quote

import httpx

from keepyourid.verification.interfaces import (
    DIDResolver,
    ResolvedDID,
)


class DIDResolutionError(Exception):
    pass


class UniversalResolver(DIDResolver):
    def __init__(
        self,
        endpoint: str,
        timeout: float = 10.0,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def resolve(self, did: str) -> ResolvedDID:
        if not did.startswith("did:"):
            raise DIDResolutionError("Invalid DID format.")

        url = (
            f"{self.endpoint}/1.0/identifiers/"
            f"{quote(did, safe=':')}"
        )

        try:
            response = httpx.get(
                url,
                timeout=self.timeout,
                headers={"Accept": "application/ld+json"},
            )
            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise DIDResolutionError(
                "Unable to resolve DID."
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise DIDResolutionError(
                "Invalid resolver response."
            ) from exc

        if payload.get("didResolutionMetadata", {}).get("error"):
            raise DIDResolutionError(
                "DID resolution failed: "
                + str(payload["didResolutionMetadata"]["error"])
            )

        document = payload.get("didDocument")

        if not isinstance(document, dict):
            raise DIDResolutionError(
                "Resolver returned no valid DID Document."
            )

        return ResolvedDID(
            did=did,
            document=document,
            metadata=payload.get("didDocumentMetadata", {}),
        )