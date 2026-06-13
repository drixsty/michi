import contextvars
from typing import Optional

# Request-local context variables
jwt_token_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("jwt_token", default=None)
org_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("org_id", default=None)
