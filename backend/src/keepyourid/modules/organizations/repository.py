from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.modules.organizations.models import Organization


class OrganizationRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Organization | None:
        return self.session.scalar(
            select(Organization).where(Organization.email == email)
        )

    def get_by_registration_number(
        self,
        registration_number: str,
    ) -> Organization | None:
        return self.session.scalar(
            select(Organization).where(
                Organization.registration_number == registration_number
            )
        )

    def create(self, organization: Organization) -> Organization:
        self.session.add(organization)
        self.session.commit()
        self.session.refresh(organization)
        return organization