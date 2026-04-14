"""
Dependency Injection Container
Construit et injecte les services avec leurs dépendances (Repositories).
"""
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

# Auth
from src.modules.auth.application.auth_service import ApplicationAuthService
from src.modules.auth.application.org_service import ApplicationOrgService
from src.modules.auth.infrastructure.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyOrganizationRepository,
    SQLAlchemyMembershipRepository,
    SQLAlchemyInvitationRepository,
)
from src.modules.auth.infrastructure.security_adapters import (
    BcryptPasswordHasher,
    JwtTokenService,
)

# Inventory
from src.modules.inventory.application.inventory_service import InventoryService
from src.modules.inventory.application.omnichannel_service import OmnichannelService
from src.modules.inventory.application.alert_service import AlertService
from src.modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from src.modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
from src.modules.inventory.infrastructure.repositories.sales_log_repository import SQLAlchemySalesLogRepository
from src.modules.inventory.infrastructure.repositories.alert_repository import SQLAlchemyAlertRepository
from src.modules.inventory.application.email_service import EmailService

# Forecasting
from src.modules.forecasting.application.forecasting_service import ForecastingService
from src.modules.forecasting.infrastructure.repositories.cleaned_demand_repository import SQLAlchemyCleanedDemandRepository
from src.modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository


@dataclass
class ServiceContainer:
    """Conteneur de services pré-configurés injecté dans GraphQLContext"""
    auth_service: ApplicationAuthService
    org_service: ApplicationOrgService
    inventory_service: InventoryService
    omnichannel_service: OmnichannelService
    alert_service: AlertService
    forecasting_service: ForecastingService


def build_services(db: AsyncSession, billing_service: Optional[object] = None) -> ServiceContainer:
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

    # Note: Email service est un service d'infrastructure pur (sans DB en général, mais utilise Config)
    email_service = EmailService()

    # 2. Adapters (Infrastructure utils)
    password_hasher = BcryptPasswordHasher()
    token_service = JwtTokenService()

    # 3. Services (Application)
    auth_service = ApplicationAuthService(
        user_repo=user_repo,
        org_repo=org_repo,
        membership_repo=membership_repo,
        password_hasher=password_hasher,
        token_service=token_service,
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
        store_repo=store_repo
    )
    
    omnichannel_service = OmnichannelService(
        product_repo=product_repo,
        store_repo=store_repo
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
        store_repo=store_repo
    )

    return ServiceContainer(
        auth_service=auth_service,
        org_service=org_service,
        inventory_service=inventory_service,
        omnichannel_service=omnichannel_service,
        alert_service=alert_service,
        forecasting_service=forecasting_service
    )
