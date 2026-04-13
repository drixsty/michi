from functools import wraps
from typing import List, Union
from src.core.exceptions import MichiException, UnauthenticatedException, ErrorCode
from src.modules.auth.models import OrganizationMember, UserRole
from sqlalchemy import select
import uuid
from loguru import logger

def require_role(allowed_roles: Union[str, List[str]]):
    """
    Décorateur pour restreindre l'accès à un résolveur GraphQL selon le rôle de l'utilisateur.
    
    Usage:
        @require_role("admin")
        async def my_resolver(self, info): ...
        
        @require_role(["admin", "manager"])
        async def my_resolver(self, info): ...
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles.lower()]
    else:
        allowed_roles = [r.lower() for r in allowed_roles]

    def decorator(f):
        @wraps(f)
        async def wrapper(self, info, *args, **kwargs):
            if not info.context.user_id or not info.context.org_id:
                raise UnauthenticatedException("Accès refusé : session ou organisation non identifiée")
                
            db = info.context.db
            user_id = uuid.UUID(str(info.context.user_id))
            org_id = uuid.UUID(str(info.context.org_id))
            
            # 1. Récupérer le rôle du membre dans l'organisation
            result = await db.execute(
                select(OrganizationMember).where(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id
                )
            )
            member = result.scalar_one_or_none()
            
            if not member:
                raise MichiException(
                    message="Vous n'êtes pas membre de cette organisation", 
                    code=ErrorCode.FORBIDDEN
                )
            
            # 2. Vérification du rôle
            # member.role est un enum UserRole
            user_role = member.role.value if hasattr(member.role, 'value') else str(member.role).lower()
            
            if user_role not in allowed_roles:
                logger.warning(f"Accès refusé [Role Guard] : User {user_id} (Role: {user_role}) tente d'accéder à une fonction réservée à {allowed_roles}")
                raise MichiException(
                    message=f"Cette action nécessite un rôle parmi : {', '.join(allowed_roles)}", 
                    code=ErrorCode.FORBIDDEN
                )
            
            return await f(self, info, *args, **kwargs)
        return wrapper
    return decorator
