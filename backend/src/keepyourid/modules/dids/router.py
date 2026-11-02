
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.core.dependencies import get_db
from keepyourid.modules.dids.challenge_service import (
    DIDChallengeAlreadyConsumedError,
    DIDChallengeExpiredError,
    DIDChallengeService,
    DIDChallengeWrongContextError,
    DIDChallengeWrongDIDError,
    DIDNotFoundError,
)
from keepyourid.modules.dids.models import DID
from keepyourid.modules.dids.schemas import (
    DIDChallengeCreate,
    DIDChallengeResponse,
    DIDCreate,
    DIDProofSubmission,
    DIDResponse,
    DIDVerificationResponse,
)
from keepyourid.modules.dids.service import (
    DIDAlreadyExistsError,
    DIDAlreadyVerifiedError,
    DIDService,
    OrganizationInactiveError,
    OrganizationNotFoundError,
)
from keepyourid.modules.dids.verification.resolver import (
    UniversalResolver,
)
from keepyourid.modules.dids.verification.service import (
    DIDVerificationError,
    DIDVerificationService,
)
from keepyourid.modules.dids.verification.signature import (
    build_authentication_message,
)

router = APIRouter(prefix="/dids", tags=["DIDs"])


def get_did_verifier() -> DIDVerificationService:
    endpoint = os.getenv("DID_RESOLVER_URL")

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DID resolver is not configured.",
        )

    return DIDVerificationService(
        resolver=UniversalResolver(endpoint=endpoint),
    )


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
):
    try:
        result = DIDService(db).verify_control(
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
