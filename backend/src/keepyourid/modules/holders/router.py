from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.core.auth import get_current_user
from keepyourid.core.dependencies import get_db
from keepyourid.modules.credentials.schemas import CredentialResponse
from keepyourid.modules.holders.challenge_service import (
    HolderDIDChallengeExpiredError,
    HolderDIDChallengeWrongContextError,
    HolderDIDNotFoundError,
)
from keepyourid.modules.holders.schemas import (
    HolderDIDChallengeCreate,
    HolderDIDChallengeResponse,
    HolderDIDCreate,
    HolderDIDProofSubmission,
    HolderDIDResponse,
    HolderDIDVerificationResponse,
)
from keepyourid.modules.holders.service import (
    HolderDIDAlreadyExistsError,
    HolderDIDService,
    HolderUserNotFoundError,
)
from keepyourid.modules.users.models import User

router = APIRouter(prefix="/holders", tags=["Holders"])


@router.get("/me/dids", response_model=list[HolderDIDResponse])
def list_holder_dids(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return HolderDIDService(db).list_user_dids(current_user.id)


@router.post("/me/dids", response_model=HolderDIDResponse, status_code=status.HTTP_201_CREATED)
def register_holder_did(
    data: HolderDIDCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return HolderDIDService(db).register_user_did(
            user_id=current_user.id,
            identifier=data.identifier,
            method=data.method,
            document=data.document,
        )
    except HolderUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HolderDIDAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/me/dids/{did_id}/challenges", response_model=HolderDIDChallengeResponse)
def create_holder_did_challenge(
    did_id: UUID,
    data: HolderDIDChallengeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HolderDIDService(db)
    did = service.get_user_did(current_user.id, did_id)
    if did is None:
        raise HTTPException(status_code=404, detail="Holder DID not found.")

    from keepyourid.modules.holders.challenge_service import HolderDIDChallengeService

    challenge = HolderDIDChallengeService(db).create_challenge(
        did_id,
        purpose=data.purpose,
        domain=data.domain,
    )
    message = (
        "did:ethr:sepolia:"
        f"{did.identifier} challenge {challenge.challenge} purpose {challenge.purpose} "
        f"domain {challenge.domain} issued_at {challenge.issued_at.isoformat()} "
        f"expires_at {challenge.expires_at.isoformat()}"
    )
    return HolderDIDChallengeResponse(
        challenge_id=challenge.id,
        challenge=challenge.challenge,
        purpose=challenge.purpose,
        domain=challenge.domain,
        issued_at=challenge.issued_at,
        expires_at=challenge.expires_at,
        message=message,
    )


@router.post("/me/dids/{did_id}/verify", response_model=HolderDIDVerificationResponse)
def verify_holder_did(
    did_id: UUID,
    data: HolderDIDProofSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HolderDIDService(db)
    did = service.get_user_did(current_user.id, did_id)
    if did is None:
        raise HTTPException(status_code=404, detail="Holder DID not found.")

    try:
        result = service.verify_holder_did(
            did_id=did.id,
            challenge_id=data.challenge_id,
            signature=data.signature,
            verification_method=data.verification_method,
            purpose=data.purpose,
            domain=data.domain,
            did_document=did.document,
        )
        return HolderDIDVerificationResponse(**result)
    except HolderDIDNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (HolderDIDChallengeExpiredError, HolderDIDChallengeWrongContextError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/me/credentials", response_model=list[CredentialResponse])
def list_holder_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return HolderDIDService(db).list_user_credentials(current_user.id)
