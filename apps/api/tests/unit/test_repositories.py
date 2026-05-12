import pytest
from uuid import uuid4
from modules.auth.infrastructure.repositories import SQLAlchemyUserRepository, SQLAlchemyOrganizationRepository
from core.database.models import User, Organization
from modules.auth.domain.value_objects import Email

@pytest.mark.asyncio
async def test_user_repository_save_and_get(db_session):
    repo = SQLAlchemyUserRepository(db_session)
    
    # Create a user model
    user_id = uuid4()
    user_model = User(
        id=user_id,
        email="test_repo@example.com",
        first_name="Test",
        last_name="Repo"
    )
    
    # Save via repository
    entity = await repo.save(user_model)
    assert entity.email.value == "test_repo@example.com"
    
    # Get by ID
    retrieved = await repo.get_by_id(user_id)
    assert retrieved is not None
    assert retrieved.first_name == "Test"
    
    # Get by Email
    retrieved_email = await repo.get_by_email(Email("test_repo@example.com"))
    assert retrieved_email is not None
    assert retrieved_email.id == user_id

@pytest.mark.asyncio
async def test_organization_repository_save_and_get(db_session):
    repo = SQLAlchemyOrganizationRepository(db_session)
    
    org_id = uuid4()
    org_model = Organization(
        id=org_id,
        name="Test Org",
        slug="test-org"
    )
    
    # Save
    entity = await repo.save(org_model)
    assert entity.name == "Test Org"
    
    # Get by ID
    retrieved = await repo.get_by_id(org_id)
    assert retrieved is not None
    assert retrieved.slug.value == "test-org"
