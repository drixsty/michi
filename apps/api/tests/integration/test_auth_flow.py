import pytest
import pyotp
from core.di import build_services
from core.database.models import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_complete_auth_and_2fa_flow(db_session):
    """
    Test complet du flux d'authentification et activation 2FA.
    """
    from core.database.models import User
    from modules.auth.infrastructure.security_adapters import BcryptPasswordHasher
    import uuid
    
    # 0. Créer l'utilisateur dans la DB de test
    user_id = uuid.UUID("c946f5b8-662a-4808-8acf-d58b4dab49bc")
    hasher = BcryptPasswordHasher()
    test_user = User(
        id=user_id,
        email="test@michi.com",
        hashed_password=hasher.hash("password123"),
        is_active=True
    )
    db_session.add(test_user)
    await db_session.commit()

    services = build_services(db_session)
    auth_service = services.auth_service
    user_id_str = str(user_id)
    
    # 1. Login initial
    print("[TEST] Testing login...")
    auth_result = await auth_service.login("test@michi.com", "password123")
    assert auth_result.token is not None
    
    # 2. Setup 2FA
    print("[TEST] Testing 2FA Setup...")
    setup_data = await auth_service.setup_2fa(user_id_str)
    assert "secret" in setup_data
    assert "qr_code" in setup_data
    secret = setup_data["secret"]
    
    # 3. Confirm 2FA (Verification avec un code valide)
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    print(f"[TEST] Confirming 2FA with code {code}...")
    success = await auth_service.confirm_2fa(user_id_str, code)
    assert success is True
    
    # 4. Vérifier que l'utilisateur a bien le 2FA activé en base
    stmt = select(User).where(User.email == "dev@michi.com")
    result = await db_session.execute(stmt)
    user = result.scalar()
    assert user.two_factor_enabled is True
    assert user.two_factor_secret == secret
    
    print("[TEST] Auth & 2FA Flow validated! ✅")
