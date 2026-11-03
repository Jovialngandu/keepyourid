from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import (
    MembershipRole,
    MembershipStatus,
    Organization,
    OrganizationMembership,
)
from keepyourid.modules.organizations.repository import OrganizationRepository
from keepyourid.modules.organizations.schemas import OrganizationCreate
from keepyourid.modules.users.models import User

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

	def list(self) -> list[Organization]:
		return self.repository.list()

	def get(self, organization_id: UUID) -> Organization | None:
		organization = self.repository.get_by_id(organization_id)
		if organization is None:
			return None
		if organization.did is None:
			related_did = (
				self.session.query(DID)
				.filter(DID.organization_id == organization_id)
				.order_by(DID.created_at.desc())
				.first()
			)
			if related_did is not None:
				organization.did = related_did.identifier
		return organization

	def register(self, data: OrganizationCreate, owner_user: User | None = None) -> Organization:
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
			created = self.repository.create(organization)
		except IntegrityError as exc:
			self.repository.session.rollback()
			raise OrganizationAlreadyExistsError(
				"An organization with these details already exists."
			) from exc

		if owner_user is not None:
			membership = OrganizationMembership(
				organization_id=created.id,
				user_id=owner_user.id,
				role=MembershipRole.OWNER,
				status=MembershipStatus.ACTIVE,
			)
			self.session.add(membership)
			self.session.commit()

		return created
			
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


class OrganizationMembershipService:
	def __init__(self, session: Session):
		self.session = session

	def list_for_user(self, user_id: UUID) -> list[OrganizationMembership]:
		statement = (
			select(OrganizationMembership)
			.where(
				OrganizationMembership.user_id == user_id,
				OrganizationMembership.status == MembershipStatus.ACTIVE,
			)
			.order_by(OrganizationMembership.created_at.desc())
		)
		return list(self.session.scalars(statement).all())

	def list_for_organization(self, organization_id: UUID) -> list[OrganizationMembership]:
		statement = (
			select(OrganizationMembership)
			.where(OrganizationMembership.organization_id == organization_id)
			.order_by(OrganizationMembership.created_at.desc())
		)
		return list(self.session.scalars(statement).all())

	def get_membership(self, membership_id: UUID) -> OrganizationMembership | None:
		return self.session.get(OrganizationMembership, membership_id)

	def ensure_user_access(self, user_id: UUID, organization_id: UUID) -> OrganizationMembership | None:
		statement = select(OrganizationMembership).where(
			OrganizationMembership.organization_id == organization_id,
			OrganizationMembership.user_id == user_id,
			OrganizationMembership.status == MembershipStatus.ACTIVE,
		)
		return self.session.scalar(statement)

	def add_member(self, organization_id: UUID, user_id: UUID, role: MembershipRole = MembershipRole.MEMBER) -> OrganizationMembership:
		membership = OrganizationMembership(
			organization_id=organization_id,
			user_id=user_id,
			role=role,
			status=MembershipStatus.ACTIVE,
		)
		self.session.add(membership)
		self.session.commit()
		self.session.refresh(membership)
		return membership

	def update_role(self, membership: OrganizationMembership, role: MembershipRole) -> OrganizationMembership:
		membership.role = role
		self.session.commit()
		self.session.refresh(membership)
		return membership

	def delete_membership(self, membership: OrganizationMembership) -> None:
		membership.status = MembershipStatus.SUSPENDED
		self.session.commit()