"""
Custom exceptions pour GraphQL
"""


class ErrorCode:
    """Codes d'erreur standardisés"""
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class MichiException(Exception):
    """
    Exception de base pour Michi.
    
    Convertie automatiquement en erreur GraphQL avec code et details.
    """
    
    def __init__(self, message: str, code: str, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class UnauthenticatedException(MichiException):
    """Token JWT invalide ou manquant"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, ErrorCode.UNAUTHENTICATED)


class ForbiddenException(MichiException):
    """Action non autorisée"""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, ErrorCode.FORBIDDEN)


class NotFoundException(MichiException):
    """Ressource non trouvée"""
    
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            f"{resource} {resource_id} not found",
            ErrorCode.NOT_FOUND,
            {"resource": resource, "id": resource_id}
        )


class ValidationException(MichiException):
    """Erreur de validation"""
    
    def __init__(self, message: str, errors: dict = None):
        super().__init__(
            message,
            ErrorCode.VALIDATION_ERROR,
            {"errors": errors or {}}
        )
