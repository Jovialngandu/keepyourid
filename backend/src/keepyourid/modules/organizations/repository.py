from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.modules.organizations.models import Organization


class OrganizationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, organization_id: UUID) -> Organization | None:
        return self.session.get(Organization, organization_id)

    def list(self) -> list[Organization]:
        statement = select(Organization).order_by(
            Organization.created_at.desc()
        )
        return list(self.session.scalars(statement).all())

    def list_by_ids(self, organization_ids: list[UUID]) -> list[Organization]:
        if not organization_ids:
            return []

        statement = (
            select(Organization)
            .where(Organization.id.in_(organization_ids))
            .order_by(Organization.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

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
