
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from keepyourid.core.dependencies import get_db
from keepyourid.modules.credentials.schemas import (
    CredentialCreate,
    CredentialResponse,
)
from keepyourid.modules.credentials.service import (
    CredentialAlreadyExistsError,
    CredentialDIDNotFoundError,
    CredentialDIDNotVerifiedError,
    CredentialInvalidDataError,
    CredentialOrganizationInactiveError,
    CredentialOrganizationNotFoundError,
    CredentialService,
)

from keepyourid.modules.credentials.schemas import (
    CredentialSigningRequest,
    CredentialIssuanceRequest,
)


from keepyourid.modules.credentials.schemas import (
    CredentialIssuancePreparationResponse,
    CredentialIssuanceCompletion,
    CredentialIssuanceResponse,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/credentials",
    tags=["Credentials"],
)


def get_credential_service(db: Session = Depends(get_db)):
    return CredentialService(db)


@router.post(
    "",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_credential(
    organization_id: UUID,
    data: CredentialCreate,
    service: CredentialService = Depends(get_credential_service),
):
    try:
        return service.create_draft(organization_id, data)

    except CredentialOrganizationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except CredentialDIDNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except CredentialOrganizationInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except CredentialDIDNotVerifiedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except CredentialInvalidDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except CredentialAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[CredentialResponse],
)
def list_credentials(
    organization_id: UUID,
    service: CredentialService = Depends(get_credential_service),
):
    try:
        return service.list_by_organization(organization_id)
    except CredentialOrganizationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{credential_id}",
    response_model=CredentialResponse,
)
def get_credential(
    organization_id: UUID,
    credential_id: UUID,
    service: CredentialService = Depends(get_credential_service),
):
    credential = service.get(credential_id, organization_id)

    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found.",
        )

    return credential


@router.post(
    "/{credential_id}/prepare-issuance",
    response_model=CredentialIssuancePreparationResponse,
)
def prepare_credential_issuance(
    organization_id: UUID,
    credential_id: UUID,
    service: CredentialService = Depends(get_credential_service),
):
    try:
        return service.prepare_issuance(
            credential_id=credential_id,
            organization_id=organization_id,
        )
    except CredentialInvalidDataError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(exc) == "Credential not found."
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc


@router.post(
    "/{credential_id}/complete-issuance",
    response_model=CredentialIssuanceResponse,
)
def complete_credential_issuance(
    organization_id: UUID,
    credential_id: UUID,
    data: CredentialIssuanceCompletion,
    service: CredentialService = Depends(get_credential_service),
):
    try:
        return service.complete_issuance(
            credential_id=credential_id,
            signature=data.signature,
            key_id=data.key_id,
            organization_id=organization_id,
        )
    except CredentialInvalidDataError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(exc) == "Credential not found."
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc