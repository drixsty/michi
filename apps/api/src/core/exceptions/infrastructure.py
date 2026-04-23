from .base import MichiException
from typing import Any, Dict, Optional

class InfrastructureError(MichiException):
    """Raised when an external service or DB fails."""
    def __init__(self, message: str, service: str):
        super().__init__(message, code="INFRASTRUCTURE_ERROR", details={"service": service})

class NotFoundError(MichiException):
    """Raised when a resource is not found."""
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            f"{resource_type} with id {resource_id} not found", 
            code="NOT_FOUND", 
            details={"type": resource_type, "id": str(resource_id)}
        )
