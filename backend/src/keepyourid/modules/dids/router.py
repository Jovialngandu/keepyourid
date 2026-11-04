
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.blockchain.abi import load_issuer_registry_abi
from keepyourid.blockchain.adapters.ethereum_adapter import EthereumAdapter
from keepyourid.blockchain.config import get_blockchain_config
from keepyourid.blockchain.repositories.transaction_repository import (
    TransactionRepository,
)
from keepyourid.blockchain.services.issuer_registry_service import (
    IssuerRegistryService,
)
from keepyourid.blockchain.signers.local_signer import LocalAccountSigner
from keepyourid.core.dependencies import get_db
from keepyourid.modules.dids.challenge_service import (
    DIDChallengeAlreadyConsumedError,
    DIDChallengeExpiredError,
    DIDChallengeService,
    DIDChallengeWrongContextError,
    DIDChallengeWrongDIDError,
    DIDNotFoundError,
)

from keepyourid.modules.dids.service import (
    DIDAlreadyExistsError,
    DIDAlreadyVerifiedError,
    DIDService,
    OrganizationInactiveError,
    OrganizationNotFoundError,
)
from keepyourid.verification.did.resolver import (
    UniversalResolver,
)
from keepyourid.verification.did.service import (
    DIDVerificationError,
    DIDVerificationService,
)
from keepyourid.verification.did.signature import (
    build_authentication_message,
)

from keepyourid.modules.dids.schemas import (
    DIDBlockchainStatusResponse,
    DIDChallengeCreate,
    DIDChallengeResponse,
    DIDCreate,
    DIDListResponse,
    DIDProofSubmission,
    DIDResponse,
    DIDVerificationResponse,
)

from keepyourid.config import get_settings


router = APIRouter(prefix="/dids", tags=["DIDs"])


# def get_did_verifier() -> DIDVerificationService:
#     endpoint = os.getenv("DID_RESOLVER_URL")

#     if not endpoint:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="DID resolver is not configured.",
#         )

#     return DIDVerificationService(
#         resolver=UniversalResolver(endpoint=endpoint),
#     )


def get_did_verifier() -> DIDVerificationService:
    return DIDVerificationService()


def get_issuer_registry_service(
    db: Session = Depends(get_db),
) -> IssuerRegistryService | None:

    settings = get_settings()

    print("[BLOCKCHAIN] Private key configured:",
          settings.blockchain_private_key is not None)

    try:
        config = get_blockchain_config()
        print("[BLOCKCHAIN] RPC:", config.rpc_url)
        print("[BLOCKCHAIN] Chain ID:", config.chain_id)
        print("[BLOCKCHAIN] Registry:", config.registry_address)

    except RuntimeError as exc:
        print("[BLOCKCHAIN] Configuration error:", exc)
        return None

    if settings.blockchain_private_key is None:
        print("[BLOCKCHAIN] Missing private key")
        return None

    private_key = settings.blockchain_private_key.get_secret_value()

    adapter = EthereumAdapter(
        config,
        load_issuer_registry_abi(),
    )

    signer = LocalAccountSigner(private_key)

    print("[BLOCKCHAIN] Signer:", signer.address)

    repository = TransactionRepository(db)

    print("[BLOCKCHAIN] Issuer registry service initialized")

    return IssuerRegistryService(
        adapter=adapter,
        signer=signer,
        transaction_repository=repository,
        session=db,
    )


@router.get("/organizations/{organization_id}", response_model=DIDListResponse)
def list_dids_for_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
):
    dids = DIDService(db).list_by_organization(organization_id)
    return DIDListResponse(items=dids)


@router.get("/{did_id}", response_model=DIDResponse)
def get_did(did_id: UUID, db: Session = Depends(get_db)):
    did = DIDService(db).get(did_id)
    if did is None:
        raise HTTPException(status_code=404, detail="DID not found.")
    return did


@router.post(
    "/organizations/{organization_id}",
    response_model=DIDResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_did(
    organization_id: UUID,
    data: DIDCreate,
    db: Session = Depends(get_db),
):
    service = DIDService(db)

    try:
        return service.register(organization_id, data)

    except OrganizationNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    except OrganizationInactiveError as exc:
        raise HTTPException(409, str(exc)) from exc

    except DIDAlreadyExistsError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post(
    "/{did_id}/challenges",
    response_model=DIDChallengeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_did_challenge(
    did_id: UUID,
    data: DIDChallengeCreate,
    db: Session = Depends(get_db),
):
    try:
        did = db.get(DID, did_id)

        if did is None:
            raise DIDNotFoundError("DID not found.")

        challenge = DIDChallengeService(db).create_challenge(
            did_id,
            purpose=data.purpose,
            domain=data.domain,
        )

        message = build_authentication_message(
            did=did.identifier,
            challenge=challenge.challenge,
            purpose=challenge.purpose,
            domain=challenge.domain,
            issued_at=challenge.issued_at.isoformat(),
            expires_at=challenge.expires_at.isoformat(),
        )

        return DIDChallengeResponse(
            challenge_id=challenge.id,
            challenge=challenge.challenge,
            purpose=challenge.purpose,
            domain=challenge.domain,
            issued_at=challenge.issued_at,
            expires_at=challenge.expires_at,
            message=message,
        )

    except DIDNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    except DIDChallengeWrongContextError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post(
    "/{did_id}/verify",
    response_model=DIDVerificationResponse,
    status_code=status.HTTP_200_OK,
)
def verify_did_control(
    did_id: UUID,
    data: DIDProofSubmission,
    db: Session = Depends(get_db),
    verifier: DIDVerificationService = Depends(get_did_verifier),
    issuer_registry_service: IssuerRegistryService | None = Depends(
        get_issuer_registry_service
    ),
):
    try:
        result = DIDService(
            db,
            issuer_registry_service=issuer_registry_service,
        ).verify_control(
            did_id=did_id,
            proof=data,
            verifier=verifier,
        )

        return result

    except DIDNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    except DIDChallengeWrongDIDError as exc:
        raise HTTPException(409, str(exc)) from exc

    except DIDChallengeWrongContextError as exc:
        raise HTTPException(409, str(exc)) from exc

    except DIDChallengeAlreadyConsumedError as exc:
        raise HTTPException(409, str(exc)) from exc

    except DIDChallengeExpiredError as exc:
        raise HTTPException(410, str(exc)) from exc

    except DIDAlreadyVerifiedError as exc:
        raise HTTPException(409, str(exc)) from exc

    except DIDVerificationError as exc:
        raise HTTPException(400, str(exc)) from exc



@router.get(
    "/{did_id}/blockchain",
    response_model=DIDBlockchainStatusResponse,
)
def get_did_blockchain_status(
    did_id: UUID,
    db: Session = Depends(get_db),
    issuer_registry_service: IssuerRegistryService | None = Depends(
        get_issuer_registry_service
    ),
):
    did = DIDService(db).get(did_id)

    if did is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DID not found.",
        )

    if issuer_registry_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service is not configured.",
        )

    issuer = issuer_registry_service.get_issuer(did.identifier)

    if issuer is None:
        return DIDBlockchainStatusResponse(
            did_id=did.id,
            identifier=did.identifier,
            registered=False,
            active=False,
            issuer=None,
        )

    return DIDBlockchainStatusResponse(
        did_id=did.id,
        identifier=did.identifier,
        registered=True,
        active=issuer["status"] == "ACTIVE",
        issuer=issuer,
    )