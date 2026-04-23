from cryptography.fernet import Fernet
import os
from typing import Optional
from core.config import settings
from core.exceptions import InfrastructureError

class EncryptionService:
    """
    Service de chiffrement symétrique pour les secrets (Credentials).
    Utilise AES-128 en mode CBC avec HMAC via l'implémentation Fernet.
    """
    
    def __init__(self, key: Optional[str] = None):
        # On utilise la clé fournie ou celle des settings (env)
        self.key = key or settings.MASTER_ENCRYPTION_KEY
        if not self.key:
            # En développement, on peut générer une clé si manquante, 
            # mais en prod c'est une erreur critique.
            if settings.ENV == "production":
                raise InfrastructureError("MASTER_ENCRYPTION_KEY is not set in production!", service="Security")
            self.key = Fernet.generate_key().decode()
            
        try:
            self.cipher = Fernet(self.key.encode())
        except Exception as e:
            raise InfrastructureError(f"Invalid encryption key: {str(e)}", service="Security")

    def encrypt(self, plain_text: str) -> str:
        """Chiffre une chaîne de caractères."""
        if not plain_text:
            return ""
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt(self, cipher_text: str) -> str:
        """Déchiffre une chaîne de caractères."""
        if not cipher_text:
            return ""
        try:
            return self.cipher.decrypt(cipher_text.encode()).decode()
        except Exception:
            # En cas d'erreur (clé changée ou donnée corrompue)
            raise InfrastructureError("Failed to decrypt secret. Check MASTER_ENCRYPTION_KEY.", service="Security")

# Instance singleton
encryption_service = EncryptionService()
