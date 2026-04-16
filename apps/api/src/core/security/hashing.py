from passlib.context import CryptContext

# Context pour hashing passwords (bcrypt)
# Sprint 21: Configuration explicite pour assurer la compatibilité entre environnements
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def hash_password(password: str) -> str:
    """Hash un password avec bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un password contre son hash."""
    return pwd_context.verify(plain_password, hashed_password)
