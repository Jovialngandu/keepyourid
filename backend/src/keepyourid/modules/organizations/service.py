from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization
from keepyourid.modules.organizations.repository import OrganizationRepository
from keepyourid.modules.organizations.schemas import OrganizationCreate


class OrganizationAlreadyExistsError(Exception):
    pass


class OrganizationService:

    def __init__(self, session: Session):
        self.repository = OrganizationRepository(session)

    def register(self, data: OrganizationCreate) -> Organization:
        email = str(data.email).strip().lower()
        registration_number = data.registration_number.strip()

        if self.repository.get_by_email(email):
            raise OrganizationAlreadyExistsError(
                "An organization with this email already exists."
            )

        if self.repository.get_by_registration_number(registration_number):
            raise OrganizationAlreadyExistsError(
                "An organization with this registration number already exists."
            )

        organization = Organization(
            legal_name=data.legal_name.strip(),
            registration_number=registration_number,
            email=email,
            phone=data.phone,
            status=OrganizationStatus.PENDING,
        )

        try:
            return self.repository.create(organization)
        except IntegrityError as exc:
            self.repository.session.rollback()
            raise OrganizationAlreadyExistsError(
                "An organization with these details already exists."
            ) from exc