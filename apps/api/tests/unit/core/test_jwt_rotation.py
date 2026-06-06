import pytest
from jose import JWTError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from core.config.settings import settings
from core.security.tokens import (
    create_access_token,
    decode_access_token,
    create_refresh_token,
    decode_refresh_token,
)

def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem


def test_jwt_hs256_fallback(monkeypatch):
    # Enforce HS256
    monkeypatch.setattr(settings, "ALGORITHM", "HS256")
    monkeypatch.setattr(settings, "JWT_PRIVATE_KEY", "")
    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY", "")
    monkeypatch.setattr(settings, "JWT_OLD_PUBLIC_KEYS", "")
    
    # Sign token
    token = create_access_token({"sub": "user_hs"})
    # Verify token
    payload = decode_access_token(token)
    assert payload["sub"] == "user_hs"
    
    # Test refresh token
    ref_token = create_refresh_token("user_hs_ref")
    uid = decode_refresh_token(ref_token)
    assert uid == "user_hs_ref"


def test_jwt_rs256_encoding_decoding(monkeypatch):
    private_pem, public_pem = generate_key_pair()
    
    monkeypatch.setattr(settings, "ALGORITHM", "RS256")
    monkeypatch.setattr(settings, "JWT_PRIVATE_KEY", private_pem)
    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY", public_pem)
    
    # Sign token
    token = create_access_token({"sub": "user_rs"})
    # Verify token
    payload = decode_access_token(token)
    assert payload["sub"] == "user_rs"
    
    # Test refresh token
    ref_token = create_refresh_token("user_rs_ref")
    uid = decode_refresh_token(ref_token)
    assert uid == "user_rs_ref"


def test_jwt_rs256_key_rotation(monkeypatch):
    old_private, old_public = generate_key_pair()
    new_private, new_public = generate_key_pair()
    
    # Sign token with old key
    monkeypatch.setattr(settings, "ALGORITHM", "RS256")
    monkeypatch.setattr(settings, "JWT_PRIVATE_KEY", old_private)
    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY", old_public)
    token = create_access_token({"sub": "user_rotated"})
    
    # Verify token using new key as primary public key, and old key as backup/old key
    monkeypatch.setattr(settings, "JWT_PRIVATE_KEY", new_private)
    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY", new_public)
    monkeypatch.setattr(settings, "JWT_OLD_PUBLIC_KEYS", old_public)
    
    # This should succeed due to old public key fallback
    payload = decode_access_token(token)
    assert payload["sub"] == "user_rotated"
    
    # If old public key is removed from rotation list, it should fail
    monkeypatch.setattr(settings, "JWT_OLD_PUBLIC_KEYS", "")
    with pytest.raises(JWTError):
        decode_access_token(token)
