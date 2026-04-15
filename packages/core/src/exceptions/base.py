class MichiException(Exception):
    """
    Exception de base pour Michi.
    Convertie automatiquement en erreur GraphQL avec code et details.
    """
    def __init__(self, message: str, code: str, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)
