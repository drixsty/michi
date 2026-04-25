"""
Dependency Injection Container
Construit et injecte les services avec leurs dépendances (Repositories).
"""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

# Auth
from modules.auth.application.auth_service import ApplicationAuthService
from modules.auth.application.org_service import ApplicationOrgService
from modules.auth.infrastructure.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyOrganizationRepository,
    SQLAlchemyMembershipRepository,
    SQLAlchemyInvitationRepository,
)
from modules.auth.infrastructure.security_adapters import (
    BcryptPasswordHasher,
    JwtTokenService,
)

# Inventory
from modules.inventory.application.inventory_service import InventoryService
from modules.inventory.application.omnichannel_service import OmnichannelService
from modules.inventory.application.alert_service import AlertService
from modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
from modules.inventory.infrastructure.repositories.sales_log_repository import SQLAlchemySalesLogRepository
from modules.inventory.infrastructure.repositories.alert_repository import SQLAlchemyAlertRepository
from modules.inventory.infrastructure.repositories.supplier_repository import SQLAlchemySupplierRepository
from modules.inventory.infrastructure.repositories.purchase_order_repository import SQLAlchemyPurchaseOrderRepository
from modules.inventory.application.email_service import EmailService

# Forecasting
from modules.forecasting.application.forecasting_service import ForecastingService
from modules.forecasting.infrastructure.repositories.cleaned_demand_repository import SQLAlchemyCleanedDemandRepository
# Decisions
from modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository

# Intelligence
from modules.intelligence.services.supplier_analysis import SupplierAnalysisService

# Decisions
from modules.decisions.application.decisions_service import ApplicationDecisionsService

# Billing
from modules.billing.application.service import ApplicationBillingService
from modules.billing.infrastructure.stripe_provider import StripeBillingProvider
from modules.billing.infrastructure.repositories import SQLAlchemyBillingRepository


@dataclass
class ServiceContainer:
    """Conteneur de services pré-configurés injecté dans GraphQLContext"""
    auth_service: ApplicationAuthService
    org_service: ApplicationOrgService
    inventory_service: InventoryService
    omnichannel_service: OmnichannelService
    alert_service: AlertService
    forecasting_service: ForecastingService
    decisions_service: ApplicationDecisionsService
    billing_service: ApplicationBillingService
    supplier_analysis_service: SupplierAnalysisService


def build_services(db: AsyncSession) -> ServiceContainer:
    """
    Factory qui construit tous les repositories et services application.
    """
    # 1. Repositories (Infrastructure)
    # Auth
    user_repo = SQLAlchemyUserRepository(db)
    org_repo = SQLAlchemyOrganizationRepository(db)
    membership_repo = SQLAlchemyMembershipRepository(db)
    invitation_repo = SQLAlchemyInvitationRepository(db)
    
    # Inventory
    product_repo = SQLAlchemyProductRepository(db)
    store_repo = SQLAlchemyStoreRepository(db)
    sales_log_repo = SQLAlchemySalesLogRepository(db)
    alert_repo = SQLAlchemyAlertRepository(db)
    
    # Forecasting
    cleaned_demand_repo = SQLAlchemyCleanedDemandRepository(db)
    prediction_repo = SQLAlchemyPredictionRepository(db)
    
    # Inventory (PO)
    po_repo = SQLAlchemyPurchaseOrderRepository(db)
    
    # Billing
    billing_repo = SQLAlchemyBillingRepository(db)

    # Inventory (supplier)
    supplier_repo = SQLAlchemySupplierRepository(db)

    # Note: Email service est un service d'infrastructure pur (sans DB en général, mais utilise Config)
    email_service = EmailService()

    # 2. Adapters (Infrastructure utils)
    password_hasher = BcryptPasswordHasher()
    token_service = JwtTokenService()

    # Billing service doit être créé avant auth/org qui en dépendent
    billing_provider = StripeBillingProvider()
    billing_service = ApplicationBillingService(
        provider=billing_provider,
        repository=billing_repo
    )

    # 3. Services (Application)
    auth_service = ApplicationAuthService(
        user_repo=user_repo,
        org_repo=org_repo,
        membership_repo=membership_repo,
        password_hasher=password_hasher,
        token_service=token_service,
        email_service=email_service,
        billing_service=billing_service
    )

    org_service = ApplicationOrgService(
        user_repo=user_repo,
        org_repo=org_repo,
        membership_repo=membership_repo,
        invitation_repo=invitation_repo,
        token_service=token_service,
        billing_service=billing_service
    )

    inventory_service = InventoryService(
        product_repo=product_repo,
        sales_log_repo=sales_log_repo,
        store_repo=store_repo,
        po_repo=po_repo
    )
    
    omnichannel_service = OmnichannelService(
        product_repo=product_repo,
        store_repo=store_repo,
        prediction_repo=prediction_repo
    )
    
    alert_service = AlertService(
        alert_repo=alert_repo,
        product_repo=product_repo,
        store_repo=store_repo,
        email_service=email_service
    )
    
    forecasting_service = ForecastingService(
        cleaned_demand_repo=cleaned_demand_repo,
        prediction_repo=prediction_repo,
        product_repo=product_repo,
        sales_log_repo=sales_log_repo,
        store_repo=store_repo,
        supplier_repo=supplier_repo
    )

    decisions_service = ApplicationDecisionsService(
        user_repo=user_repo,
        store_repo=store_repo,
        product_repo=product_repo,
        prediction_repo=prediction_repo
    )

    supplier_analysis_service = SupplierAnalysisService(db)

    return ServiceContainer(
        auth_service=auth_service,
        org_service=org_service,
        inventory_service=inventory_service,
        omnichannel_service=omnichannel_service,
        alert_service=alert_service,
        forecasting_service=forecasting_service,
        decisions_service=decisions_service,
        billing_service=billing_service,
        supplier_analysis_service=supplier_analysis_service
    )
