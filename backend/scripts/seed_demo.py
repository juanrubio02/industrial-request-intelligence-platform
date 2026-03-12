from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.infrastructure.auth.password import ScryptPasswordHasher
from app.infrastructure.database.models.organization import OrganizationModel
from app.infrastructure.database.models.organization_membership import (
    OrganizationMembershipModel,
)
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.session import get_session_factory


DEMO_ORGANIZATION_NAME = os.getenv("DEMO_ORGANIZATION_NAME", "Acme Industrial")
DEMO_ORGANIZATION_SLUG = os.getenv("DEMO_ORGANIZATION_SLUG", "acme-industrial")
DEMO_USER_EMAIL = os.getenv("DEMO_USER_EMAIL", "admin@acme.com")
DEMO_USER_FULL_NAME = os.getenv("DEMO_USER_FULL_NAME", "Admin Acme")
DEMO_USER_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "Admin1234")
DEMO_USER_ROLE = OrganizationMembershipRole(
    os.getenv("DEMO_USER_ROLE", OrganizationMembershipRole.OWNER.value)
)


async def main() -> None:
    documents_dir = Path("storage/documents")
    documents_dir.mkdir(parents=True, exist_ok=True)

    session_factory = get_session_factory()
    password_hasher = ScryptPasswordHasher()

    async with session_factory() as session:
        organization = (
            await session.execute(
                select(OrganizationModel).where(
                    OrganizationModel.slug == DEMO_ORGANIZATION_SLUG
                )
            )
        ).scalar_one_or_none()
        if organization is None:
            organization = OrganizationModel(
                id=uuid4(),
                name=DEMO_ORGANIZATION_NAME,
                slug=DEMO_ORGANIZATION_SLUG,
                is_active=True,
            )
            session.add(organization)
            await session.flush()

        user = (
            await session.execute(
                select(UserModel).where(UserModel.email == DEMO_USER_EMAIL)
            )
        ).scalar_one_or_none()
        if user is None:
            user = UserModel(
                id=uuid4(),
                email=DEMO_USER_EMAIL,
                full_name=DEMO_USER_FULL_NAME,
                password_hash=password_hasher.hash(DEMO_USER_PASSWORD),
                is_active=True,
            )
            session.add(user)
            await session.flush()
        else:
            user.full_name = DEMO_USER_FULL_NAME
            user.password_hash = password_hasher.hash(DEMO_USER_PASSWORD)
            user.is_active = True
            await session.flush()

        membership = (
            await session.execute(
                select(OrganizationMembershipModel).where(
                    OrganizationMembershipModel.organization_id == organization.id,
                    OrganizationMembershipModel.user_id == user.id,
                    OrganizationMembershipModel.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if membership is None:
            membership = OrganizationMembershipModel(
                id=uuid4(),
                organization_id=organization.id,
                user_id=user.id,
                role=DEMO_USER_ROLE,
                is_active=True,
            )
            session.add(membership)
        else:
            membership.role = DEMO_USER_ROLE
            membership.is_active = True

        await session.commit()

    print("Demo workspace is ready.")
    print(f"Organization: {DEMO_ORGANIZATION_NAME} ({DEMO_ORGANIZATION_SLUG})")
    print(f"Email: {DEMO_USER_EMAIL}")
    print(f"Password: {DEMO_USER_PASSWORD}")
    print(f"Role: {DEMO_USER_ROLE.value}")


if __name__ == "__main__":
    asyncio.run(main())
