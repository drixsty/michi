"""
Tests Value Objects Auth — Sprint 21.

Teste Email, HashedPassword, OrgSlug, JwtToken.
Couverture : validation + cas limites + comportements métier.
"""
import pytest

from src.modules.auth.domain.value_objects import Email, HashedPassword, JwtToken, OrgSlug


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

class TestEmail:
    def test_valid_email(self) -> None:
        email = Email("alice@example.com")
        assert email.value == "alice@example.com"

    def test_valid_email_with_plus(self) -> None:
        email = Email("alice+tag@example.co.uk")
        assert email.value == "alice+tag@example.co.uk"

    def test_invalid_email_no_at(self) -> None:
        with pytest.raises(ValueError, match="Email invalide"):
            Email("notanemail")

    def test_invalid_email_no_tld(self) -> None:
        with pytest.raises(ValueError, match="Email invalide"):
            Email("user@domain")

    def test_invalid_email_empty(self) -> None:
        with pytest.raises(ValueError, match="Email invalide"):
            Email("")

    def test_domain_property(self) -> None:
        email = Email("alice@michi.com")
        assert email.domain == "michi.com"

    def test_str_representation(self) -> None:
        email = Email("alice@example.com")
        assert str(email) == "alice@example.com"

    def test_equality(self) -> None:
        assert Email("a@b.com") == Email("a@b.com")

    def test_inequality(self) -> None:
        assert Email("a@b.com") != Email("c@b.com")


# ---------------------------------------------------------------------------
# HashedPassword
# ---------------------------------------------------------------------------

class TestHashedPassword:
    _VALID_HASH = "$2b$12$" + "x" * 53

    def test_valid_bcrypt_hash_2b(self) -> None:
        hp = HashedPassword(self._VALID_HASH)
        assert hp.value == self._VALID_HASH

    def test_valid_bcrypt_hash_2a(self) -> None:
        hp = HashedPassword("$2a$12$" + "x" * 53)
        assert hp.value.startswith("$2a$")

    def test_invalid_not_bcrypt(self) -> None:
        with pytest.raises(ValueError, match="bcrypt"):
            HashedPassword("sha256:abc123")

    def test_repr_masks_value(self) -> None:
        hp = HashedPassword(self._VALID_HASH)
        assert "***" in repr(hp)
        assert self._VALID_HASH not in repr(hp)

    def test_str_masks_value(self) -> None:
        hp = HashedPassword(self._VALID_HASH)
        assert str(hp) == "***"


# ---------------------------------------------------------------------------
# OrgSlug
# ---------------------------------------------------------------------------

class TestOrgSlug:
    def test_valid_slug(self) -> None:
        slug = OrgSlug("my-company")
        assert slug.value == "my-company"

    def test_valid_slug_with_numbers(self) -> None:
        slug = OrgSlug("shop-42-fr")
        assert slug.value == "shop-42-fr"

    def test_invalid_slug_uppercase(self) -> None:
        with pytest.raises(ValueError, match="Slug invalide"):
            OrgSlug("My-Company")

    def test_invalid_slug_starts_with_dash(self) -> None:
        with pytest.raises(ValueError, match="Slug invalide"):
            OrgSlug("-mycompany")

    def test_invalid_slug_too_short(self) -> None:
        with pytest.raises(ValueError, match="Slug invalide"):
            OrgSlug("ab")

    def test_str_representation(self) -> None:
        slug = OrgSlug("michi-hq")
        assert str(slug) == "michi-hq"


# ---------------------------------------------------------------------------
# JwtToken
# ---------------------------------------------------------------------------

_VALID_JWT = "header.payload.signature"


class TestJwtToken:
    def test_valid_jwt(self) -> None:
        token = JwtToken(_VALID_JWT)
        assert token.value == _VALID_JWT

    def test_invalid_jwt_two_segments(self) -> None:
        with pytest.raises(ValueError, match="3 segments"):
            JwtToken("header.payload")

    def test_invalid_jwt_single_segment(self) -> None:
        with pytest.raises(ValueError, match="3 segments"):
            JwtToken("notsegmented")

    def test_repr_masks_value(self) -> None:
        token = JwtToken(_VALID_JWT)
        assert "***" in repr(token)
        assert _VALID_JWT not in repr(token)

    def test_equality(self) -> None:
        assert JwtToken(_VALID_JWT) == JwtToken(_VALID_JWT)
