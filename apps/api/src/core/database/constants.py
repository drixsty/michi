import enum

class UserRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"

class InvitationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class OrgPlan(enum.Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"
    TRIALING = "TRIALING"
    INCOMPLETE = "INCOMPLETE" # Ajouté pour compatibilité Stripe avancée
