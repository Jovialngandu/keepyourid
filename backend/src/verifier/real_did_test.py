from datetime import datetime, timezone, timedelta
from uuid import uuid4

from keepyourid.verification.did.resolver import UniversalResolver
from keepyourid.verification.did.service import (
    DIDVerificationService,
    DIDVerificationError,
)
from keepyourid.verification.did.signature import (
    build_authentication_message,
)


DID = "did:ethr:sepolia:0x09b263ebbff015f7d1df3463f8abb8d6382c50ef"

VERIFICATION_METHOD = f"{DID}#controller"

resolver = UniversalResolver(
    endpoint="https://thisdid.com"
)

service = DIDVerificationService(
    resolver=resolver,
)

now = datetime.now(timezone.utc)

issued_at = now
expires_at = now + timedelta(minutes=5)

challenge = str(uuid4())
purpose = "authentication"
domain = "localhost:5173"

message = build_authentication_message(
    did=DID,
    challenge=challenge,
    purpose=purpose,
    domain=domain,
    issued_at=issued_at.isoformat(),
    expires_at=expires_at.isoformat(),
)

print("\n========== KEEPYOURID AUTHENTICATION ==========")
print("\nDID:", DID)
print("Verification method:", VERIFICATION_METHOD)

print("\n========== MESSAGE TO SIGN ==========\n")
print(message)

print("\n======================================")
signature = input("\nPaste MetaMask signature: ").strip()

try:
    result = service.verify_authentication(
        did=DID,
        challenge=challenge,
        purpose=purpose,
        domain=domain,
        issued_at=issued_at,
        expires_at=expires_at,
        verification_method=VERIFICATION_METHOD,
        signature=signature,
    )

    print("\n========== VERIFICATION RESULT ==========")
    print(result)

    assert result["valid"] is True

    print("\nSUCCESS: Real DID authentication verified.")

except DIDVerificationError as exc:
    print("\nAUTHENTICATION REJECTED:", exc)