import pytest
from michi_core.exceptions import (
    MichiException, 
    ErrorCode, 
    UnauthenticatedException, 
    ForbiddenException, 
    NotFoundException, 
    ValidationException,
    SubscriptionRequiredException
)

def test_michi_exception_base():
    exc = MichiException("Custom error", ErrorCode.INTERNAL_ERROR, {"hint": "test"})
    assert str(exc) == "Custom error"
    assert exc.code == ErrorCode.INTERNAL_ERROR
    assert exc.details == {"hint": "test"}

def test_unauthenticated_exception():
    exc = UnauthenticatedException()
    assert exc.code == ErrorCode.UNAUTHENTICATED
    assert "Authentication required" in exc.message

def test_forbidden_exception():
    exc = ForbiddenException("No access")
    assert exc.code == ErrorCode.FORBIDDEN
    assert exc.message == "No access"

def test_not_found_exception():
    exc = NotFoundException("Product", "123")
    assert exc.code == ErrorCode.NOT_FOUND
    assert "Product 123 not found" in exc.message
    assert exc.details["resource"] == "Product"
    assert exc.details["id"] == "123"

def test_validation_exception():
    errors = {"email": "invalid"}
    exc = ValidationException("Invalid data", errors)
    assert exc.code == ErrorCode.VALIDATION_ERROR
    assert exc.details["errors"] == errors

def test_subscription_required_exception():
    exc = SubscriptionRequiredException()
    assert exc.code == ErrorCode.SUBSCRIPTION_REQUIRED
