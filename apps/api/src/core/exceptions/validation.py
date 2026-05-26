from .base import MichiException
from .codes import ErrorCode

class ValidationException(MichiException):
    """Erreur de validation"""
    def __init__(self, message: str, errors: dict = None):
        super().__init__(
            message,
            ErrorCode.VALIDATION_ERROR,
            {"errors": errors or {}}
        )

class DomainValidationError(ValidationException):
    """Erreur de validation de domaine"""
    pass

