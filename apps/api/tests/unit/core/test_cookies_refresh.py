import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from modules.auth.adapters.resolvers import AuthMutation
from core.graphql.context import GraphQLContext
from core.database.models import User
from core.exceptions import MichiException

@pytest.mark.asyncio
async def test_login_sets_refresh_cookie():
    # 1. Setup mocks
    mock_info = MagicMock()
    mock_info.context = MagicMock()
    mock_info.context.db = AsyncMock()
    mock_info.context.response = MagicMock()
    
    mock_user = User(
        id=uuid.uuid4(),
        email="test@michi.com",
        is_active=True,
        hashed_password="hashed"
    )
    
    mock_login_result = MagicMock()
    mock_login_result.token.value = "access_token"
    mock_login_result.user_model = mock_user
    mock_login_result.mfa_required = False
    
    mock_info.context.services.auth_service.login = AsyncMock(return_value=mock_login_result)
    
    # 2. Call resolver
    mutation = AuthMutation()
    login_input = MagicMock()
    login_input.email = "test@michi.com"
    login_input.password = "password"
    
    payload = await mutation.login(mock_info, login_input)
    
    # 3. Assertions
    assert payload.token == "access_token"
    assert mock_info.context.response.set_cookie.call_count == 1
    
    called_kwargs = mock_info.context.response.set_cookie.call_args[1]
    assert called_kwargs["key"] == "michi_refresh_token"
    assert called_kwargs["httponly"] is True
    assert called_kwargs["samesite"] == "strict"
    assert "value" in called_kwargs

@pytest.mark.asyncio
async def test_refresh_token_reads_cookie_and_rotates():
    # 1. Setup mocks
    mock_info = MagicMock()
    mock_info.context = MagicMock()
    mock_info.context.db = AsyncMock()
    mock_info.context.request = MagicMock()
    mock_info.context.response = MagicMock()
    
    uid = uuid.uuid4()
    mock_user = User(
        id=uid,
        email="test@michi.com",
        is_active=True,
        current_organization_id=uuid.uuid4()
    )
    mock_info.context.db.get.return_value = mock_user
    
    # Create a real refresh token to decode
    from core.security import create_refresh_token
    token_str = create_refresh_token(str(uid))
    
    # Mock cookie presence
    mock_info.context.request.cookies = {"michi_refresh_token": token_str}
    
    # 2. Call resolver without explicit token parameter
    mutation = AuthMutation()
    payload = await mutation.refresh_token(mock_info, token=None)
    
    # 3. Assertions
    assert payload.token is not None
    assert payload.refresh_token is not None
    
    # Verify cookie rotation occurred
    assert mock_info.context.response.set_cookie.call_count == 1
    called_kwargs = mock_info.context.response.set_cookie.call_args[1]
    assert called_kwargs["key"] == "michi_refresh_token"
    assert called_kwargs["value"] == payload.refresh_token
