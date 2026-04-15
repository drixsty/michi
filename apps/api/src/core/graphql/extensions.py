from strawberry.extensions import SchemaExtension
from loguru import logger
from core.database import Base, GUID
from core.exceptions import MichiException, UnauthenticatedException, ForbiddenException, ErrorCode

class MichiExceptionExtension(SchemaExtension):
    """
    Extension Strawberry pour gérer les exceptions Michi proprement.
    Évite les tracebacks polluants dans les logs pour les erreurs attendues (Auth, Permissions).
    """
    
    def on_operation(self):
        # Avant l'opération
        yield
        # Après l'opération
        
        result = self.execution_context.result
        if result and result.errors:
            # On filtre les erreurs pour éviter de loguer les tracebacks des exceptions métier
            for error in result.errors:
                original_error = getattr(error, "original_error", None)
                
                if isinstance(original_error, UnauthenticatedException):
                    # Log minimal pour l'authentification (Silencieux ou info)
                    logger.info(f"[Security] Unauthenticated access attempt to {self.execution_context.operation_name}")
                elif isinstance(original_error, ForbiddenException):
                    logger.warning(f"[Security] Forbidden access attempt to {self.execution_context.operation_name}")
                elif isinstance(original_error, MichiException):
                    # Log d'avertissement pour les erreurs métier sans traceback complet
                    logger.warning(f"[BusinessError] {original_error.code}: {original_error.message}")
                else:
                    # Pour les autres erreurs (Bug, DB, etc.), on laisse le comportement par défaut
                    # (logué par Strawberry/FastAPI)
                    pass
