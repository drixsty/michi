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
            from core.database.session import session_flow_id
            flow_id = session_flow_id.get()
            
            # On filtre les erreurs pour éviter de loguer les tracebacks des exceptions métier
            for error in result.errors:
                original_error = getattr(error, "original_error", None)
                
                # Ajouter le flowId si présent
                if flow_id:
                    if error.extensions is None:
                        error.extensions = {}
                    error.extensions["flowId"] = str(flow_id)
                
                if isinstance(original_error, UnauthenticatedException):
                    # Log minimal pour l'authentification (Silencieux ou info)
                    logger.info(f"[Security] Unauthenticated access attempt to {self.execution_context.operation_name}")
                elif isinstance(original_error, ForbiddenException):
                    logger.warning(f"[Security] Forbidden access attempt to {self.execution_context.operation_name}")
                elif isinstance(original_error, MichiException):
                    # Log d'avertissement pour les erreurs métier sans traceback complet
                    logger.warning(f"[BusinessError] {original_error.code}: {original_error.message}")
                
                # Mettre à jour l'extension avec les détails de MichiException
                if isinstance(original_error, MichiException):
                    if error.extensions is None:
                        error.extensions = {}
                    error.extensions.update({
                        "code": original_error.code,
                        "details": original_error.details
                    })
                elif original_error:
                    # Pour les autres erreurs (Bug, DB, etc.)
                    if error.extensions is None:
                        error.extensions = {}
                    error.extensions.update({"code": "INTERNAL_ERROR"})
                    error.message = "Internal Server Error"
