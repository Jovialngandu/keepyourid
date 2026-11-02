
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
    credential = service.get(credential_id)

    if (
        credential is None
        or credential.organization_id != organization_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found.",
        )

    return credential




@router.post("/{credential_id}/prepare-issuance")
def prepare_issuance(
    organization_id: UUID,
    credential_id: UUID,
    service: CredentialService = Depends(get_credential_service),
):
    credential = service.get(credential_id)

    if (
        credential is None
        or credential.organization_id != organization_id
    ):
        raise HTTPException(status_code=404, detail="Credential not found.")

    try:
        return service.prepare_issuance(credential_id)
    except CredentialInvalidDataError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{credential_id}/issue",
    response_model=CredentialResponse,
)
def issue_credential(
    organization_id: UUID,
    credential_id: UUID,
    data: CredentialIssuanceRequest,
    service: CredentialService = Depends(get_credential_service),
):
    credential = service.get(credential_id)

    if (
        credential is None
        or credential.organization_id != organization_id
    ):
        raise HTTPException(status_code=404, detail="Credential not found.")

    try:
        return service.complete_issuance(
            credential_id,
            data.signature,
            data.key_id,
        )
    except CredentialInvalidDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
