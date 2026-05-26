import pyotp
import uuid
import secrets
from typing import Optional, List
from sqlalchemy import select
from core.database import AsyncSessionLocal
from core.database.models import User
from passlib.context import CryptContext

# Context pour le hachage des codes de secours (même sécurité que les passwords)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TwoFactorService:
    """
    Service métier pour la gestion de la Double Authentification (2FA).
    Standard TOTP (RFC 6238).
    Version Asynchrone — Sprint 21.
    """

    @staticmethod
    def generate_secret() -> str:
        """Génère un nouveau secret Base32 aléatoire."""
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(user_email: str, secret: str) -> str:
        """
        Génère l'URL otpauth:// pour les applications type Google Authenticator.
        """
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="Michi 道"
        )

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """
        Vérifie la validité d'un code TOTP à 6 chiffres.
        """
        if not secret or not code:
            return False
        totp = pyotp.totp.TOTP(secret)
        return totp.verify(code)

    @staticmethod
    def generate_recovery_codes(count: int = 10) -> List[str]:
        """Génère une liste de codes de secours aléatoires."""
        return [secrets.token_hex(4).upper() for _ in range(count)] # 8 caractères hex

    def hash_codes(self, codes: List[str]) -> List[str]:
        """Hache une liste de codes pour le stockage."""
        return [pwd_context.hash(c) for c in codes]

    def verify_recovery_code(self, hashed_codes: List[str], plain_code: str) -> Optional[List[str]]:
        """
        Vérifie si un code de secours est valide parmi la liste hachée.
        Retourne la nouvelle liste (sans le code utilisé) si valide, sinon None.
        """
        if not hashed_codes or not plain_code:
            return None
            
        plain_code = plain_code.upper()
        for i, hashed in enumerate(hashed_codes):
            if pwd_context.verify(plain_code, hashed):
                # Code valide ! On le retire (usage unique)
                new_codes = list(hashed_codes)
                new_codes.pop(i)
                return new_codes
        return None

    async def setup_2fa(self, user_id: str, session=None) -> dict:
        """
        Initialise le processus 2FA pour un utilisateur.
        Retourne le secret et l'URI pour le QR Code.
        """
        if session is not None:
            return await self._setup_2fa_impl(user_id, session)
        async with AsyncSessionLocal() as session:
            return await self._setup_2fa_impl(user_id, session)

    async def _setup_2fa_impl(self, user_id: str, session) -> dict:
        # Conversion en UUID si nécessaire
        uid = uuid.UUID(str(user_id))
        
        stmt = select(User).where(User.id == uid)
        result = await session.execute(stmt)
        user = result.scalar()
        
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        # On génère un secret temporaire (ne pas activer 'enabled' tout de suite)
        secret = self.generate_secret()
        uri = self.get_provisioning_uri(user.email, secret)
        
        return {
            "secret": secret,
            "provisioning_uri": uri
        }

    async def confirm_2fa(self, user_id: str, secret: str, code: str, session=None) -> Optional[List[str]]:
        """
        Valide le premier code et active définitivement le 2FA.
        Retourne la liste des codes de secours (en clair) si succès, sinon None.
        """
        if not self.verify_code(secret, code):
            return None

        if session is not None:
            return await self._confirm_2fa_impl(user_id, secret, code, session)
        async with AsyncSessionLocal() as session:
            res = await self._confirm_2fa_impl(user_id, secret, code, session)
            await session.commit()
            return res

    async def _confirm_2fa_impl(self, user_id: str, secret: str, code: str, session) -> Optional[List[str]]:
        uid = uuid.UUID(str(user_id))
        stmt = select(User).where(User.id == uid)
        result = await session.execute(stmt)
        user = result.scalar()
        
        if not user:
            return None
        
        # Génération des codes de secours
        plain_recovery_codes = self.generate_recovery_codes()
        user.recovery_codes = self.hash_codes(plain_recovery_codes)
        
        user.two_factor_secret = secret
        user.two_factor_enabled = True
        return plain_recovery_codes

    async def disable_2fa(self, user_id: str, session=None) -> bool:
        """
        Désactive le 2FA.
        """
        if session is not None:
            return await self._disable_2fa_impl(user_id, session)
        async with AsyncSessionLocal() as session:
            res = await self._disable_2fa_impl(user_id, session)
            await session.commit()
            return res

    async def _disable_2fa_impl(self, user_id: str, session) -> bool:
        uid = uuid.UUID(str(user_id))
        stmt = select(User).where(User.id == uid)
        result = await session.execute(stmt)
        user = result.scalar()
        
        if not user:
            return False
        
        user.two_factor_secret = None
        user.two_factor_enabled = False
        return True
