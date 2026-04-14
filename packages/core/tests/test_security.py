import pytest
from datetime import timedelta
from michi_core.security import hash_password, verify_password, create_access_token, decode_access_token
from jose import JWTError

def test_password_hashing():
    password = "secret_password"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_jwt_token_lifecycle():
    data = {"sub": "user_123", "org_id": "org_456"}
    token = create_access_token(data)
    
    payload = decode_access_token(token)
    assert payload["sub"] == data["sub"]
    assert payload["org_id"] == data["org_id"]
    assert "exp" in payload

def test_jwt_token_expiration():
    data = {"sub": "expired_user"}
    # Create a token that expired 1 second ago
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    
    with pytest.raises(JWTError):
        decode_access_token(token)

def test_jwt_invalid_token():
    with pytest.raises(JWTError):
        decode_access_token("invalid.token.here")
