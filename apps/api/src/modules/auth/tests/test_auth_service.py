"""
Tests pour AuthService
"""
import pytest
from src.modules.auth.service import AuthService
from src.modules.auth.schemas import LoginInput
from src.core.exceptions import UnauthenticatedException


@pytest.mark.asyncio
async def test_login_success(db_session, test_user):
    """Test login avec credentials valides"""
    service = AuthService(db_session)
    
    input_data = LoginInput(
        email="test@michi.com",
        password="testpassword"
    )
    
    result = await service.login(input_data)
    
    assert result.token is not None
    assert result.user.email == "test@michi.com"
    assert result.user.id == test_user.id


@pytest.mark.asyncio
async def test_login_invalid_email(db_session):
    """Test login avec email invalide"""
    service = AuthService(db_session)
    
    input_data = LoginInput(
        email="notexist@michi.com",
        password="testpassword"
    )
    
    with pytest.raises(UnauthenticatedException):
        await service.login(input_data)


@pytest.mark.asyncio
async def test_login_invalid_password(db_session, test_user):
    """Test login avec password invalide"""
    service = AuthService(db_session)
    
    input_data = LoginInput(
        email="test@michi.com",
        password="wrongpassword"
    )
    
    with pytest.raises(UnauthenticatedException):
        await service.login(input_data)


@pytest.mark.asyncio
async def test_get_user_by_id(db_session, test_user):
    """Test récupération user par ID"""
    service = AuthService(db_session)
    
    user = await service.get_user_by_id(str(test_user.id))
    
    assert user is not None
    assert user.email == "test@michi.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session):
    """Test récupération user inexistant"""
    service = AuthService(db_session)
    
    import uuid
    user = await service.get_user_by_id(str(uuid.uuid4()))
    
    assert user is None
