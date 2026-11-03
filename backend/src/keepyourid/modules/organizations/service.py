from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization
from keepyourid.modules.organizations.repository import OrganizationRepository
from keepyourid.modules.organizations.schemas import OrganizationCreate


from uuid import UUID

from sqlalchemy.orm import Session

class OrganizationAlreadyExistsError(Exception):
	pass


class OrganizationNotFoundError(Exception):
	pass


class InvalidOrganizationTransitionError(Exception):
	pass

class OrganizationService:

	def __init__(self, session: Session):
		self.session = session
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
			
	def _get_organization(self, organization_id: UUID) -> Organization:
		organization = self.session.get(Organization, organization_id)

		if organization is None:
			raise OrganizationNotFoundError(
				f"Organization {organization_id} not found."
			)

		return organization

	def _change_status(
		self,
		organization_id: UUID,
		expected_status: OrganizationStatus,
		new_status: OrganizationStatus,
	) -> Organization:
		organization = self._get_organization(organization_id)

		if organization.status != expected_status:
			raise InvalidOrganizationTransitionError(
				f"Cannot change organization status from "
				f"{organization.status.value} to {new_status.value}."
			)

		organization.status = new_status

		self.session.commit()
		self.session.refresh(organization)

		return organization


	def suspend(self, organization_id: UUID) -> Organization:
		organization = self.session.get(Organization, organization_id)

		if organization is None:
			raise OrganizationNotFoundError("Organization not found.")

		if organization.status != OrganizationStatus.ACTIVE:
			raise InvalidOrganizationTransitionError(
				"Only active organizations can be suspended."
			)

		organization.status = OrganizationStatus.SUSPENDED

		self.session.commit()
		self.session.refresh(organization)

		return organization

	def reactivate(self, organization_id: UUID) -> Organization:
		organization = self.session.get(Organization, organization_id)

		if organization is None:
			raise OrganizationNotFoundError("Organization not found.")

		if organization.status != OrganizationStatus.SUSPENDED:
			raise InvalidOrganizationTransitionError(
				"Only suspended organizations can be reactivated."
			)

		organization.status = OrganizationStatus.ACTIVE

		self.session.commit()
		self.session.refresh(organization)

		return organization

	def approve(self, organization_id: UUID) -> Organization:
		return self._change_status(
			organization_id,
			expected_status=OrganizationStatus.PENDING,
			new_status=OrganizationStatus.ACTIVE,
		)

	def reject(self, organization_id: UUID) -> Organization:
		return self._change_status(
			organization_id,
			expected_status=OrganizationStatus.PENDING,
			new_status=OrganizationStatus.REJECTED,
		)