from keepyourid.verification.did.resolver import UniversalResolver
from keepyourid.verification.did.service import DIDVerificationService


def create_verifier() -> DIDVerificationService:
    resolver = UniversalResolver(
    endpoint="https://thisdid.com"
	)

    return DIDVerificationService(
        resolver=resolver,
    )


def main() -> None:
    verifier = create_verifier()

    print("Verification engine initialized.")
    print(f"Resolver: {verifier.resolver.__class__.__name__}")
    print(f"Method verifier: {verifier.method_verifier.__class__.__name__}")
    print(
        "Signature verifier: "
        f"{verifier.signature_verifier.__class__.__name__}"
    )


if __name__ == "__main__":
    main()