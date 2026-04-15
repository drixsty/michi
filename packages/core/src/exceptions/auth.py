from .base import MichiException
from .codes import ErrorCode

class UnauthenticatedException(MichiException):
    """Token JWT invalide ou manquant"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, ErrorCode.UNAUTHENTICATED)

class ForbiddenException(MichiException):
    """Action non autorisée"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, ErrorCode.FORBIDDEN)

class SubscriptionRequiredException(MichiException):
    """Accès restreint aux abonnés payants"""
    def __init__(self, message: str = "Un abonnement payant est requis pour cette fonctionnalité"):
        super().__init__(message, ErrorCode.SUBSCRIPTION_REQUIRED)

class NotFoundException(MichiException):
    """Ressource non trouvée"""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            f"{resource} {resource_id} not found",
            ErrorCode.NOT_FOUND,
            {"resource": resource, "id": resource_id}
        )
