"""
Value Objects du domaine Auth — Sprint 21.

Objets immuables sans identité propre. Encapsulent les règles de validation
métier sur les primitives (email, password, token).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,62}[a-z0-9]$")


@dataclass(frozen=True)
class Email:
    """
    Value object Email — valide le format à la construction.

    Example:
        >>> Email("alice@example.com")
        Email(value='alice@example.com')
        >>> Email("bad-email")  # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: Email invalide : 'bad-email'
    """

    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise ValueError(f"Email invalide : {self.value!r}")

    def __str__(self) -> str:
        return self.value

    @property
    def domain(self) -> str:
        return self.value.split("@", 1)[1]


@dataclass(frozen=True)
class HashedPassword:
    """
    Value object HashedPassword — représente un mot de passe déjà hashé (bcrypt).

    N'expose jamais le hash brut à l'extérieur du domaine.
    """

    _hash: str

    def __init__(self, hash_value: str) -> None:
        if not hash_value.startswith("$2b$") and not hash_value.startswith("$2a$"):
            raise ValueError("HashedPassword doit être un hash bcrypt valide.")
        object.__setattr__(self, "_hash", hash_value)

    @property
    def value(self) -> str:
        return self._hash

    def __repr__(self) -> str:
        return "HashedPassword(***)"

    def __str__(self) -> str:
        return "***"


@dataclass(frozen=True)
class OrgSlug:
    """
    Value object OrgSlug — identifiant URL-safe d'une organisation.

    Règle : 3-64 caractères, minuscules, chiffres, tirets, pas de tiret en début/fin.

    Example:
        >>> OrgSlug("my-company")
        OrgSlug(value='my-company')
        >>> OrgSlug("My-Company")  # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: Slug invalide : 'My-Company' ...
    """

    value: str

    def __post_init__(self) -> None:
        if not _SLUG_RE.match(self.value):
            raise ValueError(
                f"Slug invalide : {self.value!r} "
                "(3-64 chars, minuscules, chiffres, tirets, pas de tiret en début/fin)"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class JwtToken:
    """
    Value object JwtToken — enveloppe un token JWT opaque.

    Le domaine ne valide pas la signature (responsabilité de la couche infra).
    """

    value: str

    def __post_init__(self) -> None:
        parts = self.value.split(".")
        if len(parts) != 3:
            raise ValueError("JwtToken doit avoir 3 segments séparés par des points.")

    def __repr__(self) -> str:
        return "JwtToken(***)"

    def __str__(self) -> str:
        return "***"
