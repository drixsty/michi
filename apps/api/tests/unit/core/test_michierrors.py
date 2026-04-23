import pytest
from uuid import uuid4
from core.exceptions import NotFoundError, DomainValidationError

def test_exception_structure():
    err = NotFoundError("Product", "123")
    assert err.code == "NOT_FOUND"
    assert "Product" in err.message
    assert err.details["id"] == "123"

def test_validation_error():
    err = DomainValidationError("Invalid SKU", details={"sku": "BAD!!!"})
    assert err.code == "VALIDATION_ERROR"
    assert err.details["sku"] == "BAD!!!"
