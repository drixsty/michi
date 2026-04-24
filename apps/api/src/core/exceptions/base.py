class MichiException(Exception):
    """
    Exception de base pour Michi.
    Convertie automatiquement en erreur GraphQL avec code et details.
    """
    def __init__(self, message: str, code: str, details: dict = None, logging_level: str = "WARNING"):
        self.message = message
        self.code = code
        self.details = details or {}
        self.logging_level = logging_level
        super().__init__(message)
