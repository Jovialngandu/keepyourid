from typing import Protocol

from keepyourid.verification.results import ResolvedDID


class DIDResolver(Protocol):
    def resolve(self, did: str) -> ResolvedDID:
        ...