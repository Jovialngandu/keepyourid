
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keepyourid.modules.dids.models import DID
from keepyourid.modules.dids.repository import DIDRepository
from keepyourid.modules.dids.schemas import DIDCreate
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization


class OrganizationNotFoundError(Exception):
    pass


class OrganizationInactiveError(Exception):
    pass


class DIDAlreadyExistsError(Exception):
    pass


class DIDService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = DIDRepository(session)

    def register(
        self,
        organization_id: UUID,
        data: DIDCreate,
    ) -> DID:
        organization = self.session.get(Organization, organization_id)

        if organization is None:
            raise OrganizationNotFoundError("Organization not found.")

        if organization.status != OrganizationStatus.ACTIVE:
            raise OrganizationInactiveError(
                "Organization must be active to register a DID."
            )

        if self.repository.get_by_organization(organization_id):
            raise DIDAlreadyExistsError(
                "This organization already has a DID."
            )

        identifier = data.identifier.strip()

        if self.repository.get_by_identifier(identifier):
            raise DIDAlreadyExistsError(
                "This DID identifier is already registered."
            )

        did = DID(
            organization_id=organization_id,
            identifier=identifier,
            method=data.method.strip().lower(),
            document=data.document,
        )

        try:
            return self.repository.create(did)
        except IntegrityError as exc:
            self.session.rollback()
            raise DIDAlreadyExistsError(
                "The DID or organization association already exists."
            ) from exc
