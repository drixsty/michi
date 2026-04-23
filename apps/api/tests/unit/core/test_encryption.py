import pytest
from core.security.encryption import EncryptionService
from core.exceptions import InfrastructureError

def test_encryption_decryption_cycle():
    # Générer une clé pour le test
    from cryptography.fernet import Fernet
    test_key = Fernet.generate_key().decode()
    
    service = EncryptionService(key=test_key)
    secret = "michi_super_secret_token_123"
    
    # 1. Chiffrement
    encrypted = service.encrypt(secret)
    assert encrypted != secret
    assert len(encrypted) > len(secret)
    
    # 2. Déchiffrement
    decrypted = service.decrypt(encrypted)
    assert decrypted == secret

def test_decryption_failure_with_wrong_key():
    from cryptography.fernet import Fernet
    key1 = Fernet.generate_key().decode()
    key2 = Fernet.generate_key().decode()
    
    service1 = EncryptionService(key=key1)
    service2 = EncryptionService(key=key2)
    
    secret = "data"
    encrypted = service1.encrypt(secret)
    
    # Tenter de déchiffrer avec la mauvaise clé
    with pytest.raises(InfrastructureError) as exc:
        service2.decrypt(encrypted)
    assert "Failed to decrypt secret" in str(exc.value)

def test_empty_values():
    service = EncryptionService()
    assert service.encrypt("") == ""
    assert service.decrypt("") == ""
    assert service.encrypt(None) == "" # type: ignore
    assert service.decrypt(None) == "" # type: ignore
