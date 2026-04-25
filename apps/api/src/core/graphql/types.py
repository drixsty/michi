"""
Types GraphQL avec Strawberry
"""
import strawberry
import asyncio
import uuid
from typing import Optional, List
from datetime import datetime, date
from modules.auth.domain.permissions import PermissionCode, ROLE_PERMISSIONS

@strawberry.type
class TestConnectionResult:
    success: bool
    message: str
    latency_ms: Optional[int] = None

@strawberry.input
class UpdateCredentialInput:
    store_id: strawberry.ID
    access_token: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    meta_json: Optional[str] = "{}"

@strawberry.type
class CredentialType:
    id: strawberry.ID
    store_id: strawberry.ID
    api_key_last_chars: Optional[str] = None # Sécurité: ne jamais renvoyer la clé entière
    has_token: bool
    meta: str # JSON
    updated_at: datetime

@strawberry.type
class OrganizationType:
    """Type Organization GraphQL"""
    id: strawberry.ID
    name: str
    slug: str
    plan: str
    subscription_status: str
    created_at: datetime
    settings: str
    onboarding_completed: bool
    onboarding_step: str

    @classmethod
    def from_db(cls, org):
        import json
        if not org: return None
        
        from loguru import logger
        logger.debug(f"[GraphQL] Mapping Organization: ID={org.id}, Name='{org.name}'")

        def _val(v) -> str:
            """Extrait la valeur string d'un enum, value object ou string brut."""
            if hasattr(v, 'value'):
                return str(v.value)
            return str(v) if v is not None else ''

        return cls(
            id=strawberry.ID(str(org.id)),
            name=org.name or "Organisation sans nom",
            slug=_val(org.slug),
            plan=_val(org.plan),
            subscription_status=_val(org.subscription_status),
            created_at=org.created_at,
            settings=json.dumps(org.settings or {}),
            onboarding_completed=bool(getattr(org, 'onboarding_completed', False)),
            onboarding_step=str(getattr(org, 'onboarding_step', 'welcome'))
        )

@strawberry.type
class OrganizationMemberType:
    """Type OrganizationMember GraphQL (Liaison User/Org)"""
    organization_id: strawberry.ID
    user_id: strawberry.ID
    role: str
    permissions: str # JSON string
    computed_permissions: List[str] # Liste plate des permissions effectives
    organization: Optional[OrganizationType] = None
    user: Optional['UserType'] = None

    @classmethod
    def from_db(cls, member, include_org=True, include_user=False):
        import json
        if not member: return None
        
        # Determine role string
        try:
            role_val = getattr(member, 'role', 'viewer')
            if hasattr(role_val, 'value'):
                role_val = role_val.value
        except Exception:
            role_val = 'viewer'
            
        from modules.auth.domain.access_policy import AccessPolicy
        
        # Calculer les permissions effectives via le DOMAINE
        effective_perms = AccessPolicy.calculate_effective_permissions(
            str(role_val), 
            member.permissions
        )
                
        # Safety for organization link
        loaded_org = None
        if include_org:
            try:
                # Tentative d'accès sécurisée
                org_model = getattr(member, 'organization', None)
                if org_model:
                    # Vérification si c'est un proxy non chargé
                    from sqlalchemy.orm.util import was_deleted
                    if not was_deleted(org_model):
                        loaded_org = OrganizationType.from_db(org_model)
            except Exception:
                # Si erreur de chargement (DetachedInstance), on laisse loaded_org à None
                # mais l'ID restera présent pour le frontend
                pass

        # Safety for user link
        loaded_user = None
        if include_user:
            try:
                user_model = member.user
                if user_model:
                    loaded_user = UserType.from_db(user_model)
            except Exception as e:
                from loguru import logger
                logger.error(f"[GraphQL] Failed to load user for member: {str(e)}")

        # Extraction des permissions brutes pour le frontend
        member_perms_dict = member.permissions if isinstance(member.permissions, dict) else {}

        return cls(
            organization_id=strawberry.ID(str(getattr(member, 'organization_id', ''))),
            user_id=strawberry.ID(str(getattr(member, 'user_id', ''))),
            role=str(role_val).lower(),
            permissions=json.dumps(member_perms_dict),
            computed_permissions=list(effective_perms),
            organization=loaded_org,
            user=loaded_user
        )

@strawberry.type
class UserType:
    """Type User GraphQL (SaaS Version)"""
    id: strawberry.ID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    current_organization_id: Optional[strawberry.ID] = None
    created_at: datetime
    two_factor_enabled: bool
    preferences: str
    
    # List of organizations the user belongs to
    organizations: List[OrganizationMemberType]

    @strawberry.field
    async def is_admin(self, info) -> bool:
        """Détecte si l'utilisateur est admin dans l'organisation active."""
        if not info.context.org_id: return False
        active_org_id = str(info.context.org_id)
        
        for m in self.organizations:
            if str(m.organization_id) == active_org_id:
                return m.role.lower() == "admin"
        return False

    @classmethod
    def from_db(cls, user):
        import json
        if not user: return None
        
        # Handle dict preferences vs object
        prefs = getattr(user, 'preferences', {})
        if isinstance(prefs, dict):
            prefs_str = json.dumps(prefs)
        elif isinstance(prefs, str):
            prefs_str = prefs
        else:
            prefs_str = json.dumps(prefs or {})

        # Population des organisations (déjà chargées via selectinload)
        orgs_list = []
        try:
            raw_orgs = getattr(user, 'organizations', [])
            if hasattr(raw_orgs, "__iter__"):
                orgs_list = [OrganizationMemberType.from_db(m) for m in raw_orgs]
        except Exception:
            pass

        return cls(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            current_organization_id=strawberry.ID(str(user.current_organization_id)) if user.current_organization_id else None,
            two_factor_enabled=user.two_factor_enabled if hasattr(user, 'two_factor_enabled') else False,
            created_at=user.created_at,
            preferences=prefs_str,
            organizations=orgs_list
        )

from typing import Annotated

@strawberry.type
class StoreType:
    """Modèle Store (Anciennement SourceType)"""
    id: strawberry.ID
    name: str
    platform: str
    connected: bool
    last_sync_at: Optional[datetime] = None
    health_status: Optional[str] = "HEALTHY"
    organization_id: Optional[strawberry.ID] = None

    @classmethod
    def from_db(cls, store):
        if not store: return None
        return cls(
            id=strawberry.ID(str(store.id)),
            name=store.name,
            platform=store.platform.value if hasattr(store.platform, 'value') else str(store.platform),
            connected=store.connected,
            last_sync_at=store.last_sync_at,
            health_status=store.health_status,
            organization_id=strawberry.ID(str(store.organization_id)) if getattr(store, 'organization_id', None) else None
        )

@strawberry.type
class AlertType:
    id: strawberry.ID
    product_id: strawberry.ID
    type: str
    message: str
    is_read: bool
    severity: int
    created_at: datetime

    @classmethod
    def from_db(cls, alert):
        if not alert: return None
        return cls(
            id=strawberry.ID(str(alert.id)),
            product_id=strawberry.ID(str(alert.product_id)),
            type=alert.type,
            message=alert.message,
            is_read=alert.is_read,
            severity=alert.severity,
            created_at=alert.created_at
        )

@strawberry.type
class SupplierType:
    id: strawberry.ID
    name: str
    contact_email: Optional[str]
    reliability_score: float
    average_delay_days: float
    lead_time_sigma: float

    @classmethod
    def from_db(cls, supplier):
        if not supplier: return None
        return cls(
            id=strawberry.ID(str(supplier.id)),
            name=supplier.name,
            contact_email=supplier.contact_email,
            reliability_score=float(supplier.reliability_score or 1.0),
            average_delay_days=float(supplier.average_delay_days or 0.0),
            lead_time_sigma=float(getattr(supplier, 'lead_time_sigma', 0.0) or 0.0)
        )

@strawberry.type
class PurchaseOrderType:
    id: strawberry.ID
    product_id: strawberry.ID
    supplier_id: strawberry.ID
    quantity: int
    order_date: str
    expected_arrival_date: str
    actual_arrival_date: Optional[str]
    status: str

    @classmethod
    def from_db(cls, po):
        if not po: return None
        return cls(
            id=strawberry.ID(str(po.id)),
            product_id=strawberry.ID(str(po.product_id)),
            supplier_id=strawberry.ID(str(po.supplier_id)),
            quantity=po.quantity,
            order_date=str(po.order_date),
            expected_arrival_date=str(po.expected_arrival_date),
            actual_arrival_date=str(po.actual_arrival_date) if po.actual_arrival_date else None,
            status=po.status
        )

@strawberry.type
class ProductType:
    id: strawberry.ID
    store_id: strawberry.ID
    title: str
    sku: str
    lead_time: int
    moq: int
    current_stock: int
    boost_factor: float
    stock_weight: float
    cost_price: Optional[float]
    sale_price: Optional[float]
    supplier_id: Optional[strawberry.ID] = None

    @classmethod
    def from_db(cls, product):
        if not product: return None
        return cls(
            id=strawberry.ID(str(product.id)),
            store_id=strawberry.ID(str(product.store_id)),
            title=product.title,
            sku=product.sku,
            lead_time=product.lead_time,
            moq=product.moq,
            current_stock=product.current_stock,
            boost_factor=product.boost_factor if product.boost_factor is not None else 1.0,
            stock_weight=product.stock_weight if product.stock_weight is not None else 1.0,
            cost_price=product.cost_price,
            sale_price=product.sale_price,
            supplier_id=strawberry.ID(str(product.supplier_id)) if product.supplier_id else None
        )

    @strawberry.field(name="cleanedDemands")
    async def cleaned_demands(self, info) -> List[Annotated["CleanedDemandType", strawberry.lazy("src.modules.forecasting.adapters.resolvers")]]:
        from modules.forecasting.adapters.resolvers import resolve_cleaned_demands
        return await resolve_cleaned_demands(info, str(self.id), self.sku)

    @strawberry.field
    async def channels(self, info) -> List["ChannelBreakdownType"]:
        from modules.inventory.adapters.resolvers import resolve_product_channels
        return await resolve_product_channels(info, self.sku)

    @strawberry.field
    async def prediction(self, info) -> Optional[Annotated["PredictionType", strawberry.lazy("src.modules.forecasting.adapters.resolvers")]]:
        from modules.forecasting.adapters.resolvers import resolve_product_prediction
        return await resolve_product_prediction(info, str(self.id), self.sku)

    @strawberry.field
    async def supplier(self, info) -> Optional[SupplierType]:
        if not self.supplier_id: return None
        from modules.inventory.adapters.resolvers import resolve_product_supplier
        return await resolve_product_supplier(info, str(self.supplier_id))

    @strawberry.field
    async def warning_threshold(self, info) -> float:
        pred = await self.prediction(info)
        supp = await self.supplier(info)
        if not pred: return 0.0
        effective_lt = self.lead_time + (supp.average_delay_days if supp else 1)
        return pred.run_rate * effective_lt * 1.5

@strawberry.type
class ChannelBreakdownType:
    """Stock disponible sur un canal spécifique pour un SKU donné."""
    platform: str
    product_id: strawberry.ID
    current_stock: int
    lead_time: int
    moq: int
    run_rate: float
    stock_weight: float

@strawberry.type
class OmnichannelProductType:
    """Vue agrégée d'un SKU sur toutes les plateformes (US 9.1)."""
    id: strawberry.ID
    sku: str
    title: str
    total_stock: int
    channel_count: int
    has_conflict: bool
    dominant_run_rate: float
    total_reorder_quantity: int
    predicted_stockout_date: Optional[str]
    abc_rank: str
    annual_gross_profit: float
    demand_sigma: float
    channels: List[ChannelBreakdownType]

    @classmethod
    def from_dto(cls, item):
        return cls(
            id=strawberry.ID(item.channels[0].product_id) if item.channels else strawberry.ID(item.sku),
            sku=item.sku,
            title=item.title,
            total_stock=item.total_stock,
            channel_count=item.channel_count,
            has_conflict=item.has_conflict,
            dominant_run_rate=item.dominant_run_rate,
            total_reorder_quantity=item.total_reorder_quantity,
            predicted_stockout_date=str(item.predicted_stockout_date) if item.predicted_stockout_date else None,
            abc_rank=item.abc_rank,
            annual_gross_profit=item.annual_gross_profit,
            demand_sigma=item.demand_sigma,
            channels=[
                ChannelBreakdownType(
                    platform=ch.platform,
                    product_id=strawberry.ID(ch.product_id),
                    current_stock=ch.current_stock,
                    lead_time=ch.lead_time,
                    moq=ch.moq,
                    run_rate=ch.run_rate,
                    stock_weight=ch.stock_weight if ch.stock_weight is not None else 1.0,
                ) for ch in item.channels
            ]
        )

@strawberry.type
class CleanedDemandType:
    id: strawberry.ID
    product_id: strawberry.ID
    date: date
    raw_units_sold: float
    corrected_units_sold: float
    inventory_level: Optional[int] = None
    is_stockout: bool
    is_outlier: bool
    correction_type: str
    computed_at: datetime


    @classmethod
    def from_db_legacy(cls, r):
        if not r: return None
        return cls(
            id=strawberry.ID(str(r.id)),
            product_id=strawberry.ID(str(r.product_id)),
            date=r.date,
            raw_units_sold=r.raw_units_sold,
            corrected_units_sold=r.corrected_units_sold,
            inventory_level=r.inventory_level,
            is_stockout=r.is_stockout,
            is_outlier=r.is_outlier,
            correction_type=r.correction_type,
            computed_at=r.computed_at,
        )

@strawberry.type
class PredictionType:
    id: strawberry.ID
    product_id: strawberry.ID
    run_rate: float
    days_of_stock: Optional[float]
    predicted_stockout_date: Optional[date]
    reorder_quantity: int
    current_stock_snapshot: float
    lead_time_snapshot: int
    moq_snapshot: int
    mape_score: Optional[float]
    abc_rank: Optional[str]
    annual_gross_profit: Optional[float]
    demand_sigma: float
    computed_at: datetime

    @classmethod
    def from_db(cls, r):
        if not r: return None
        return cls(
            id=strawberry.ID(str(r.id)),
            product_id=strawberry.ID(str(r.product_id)),
            run_rate=r.run_rate,
            days_of_stock=r.days_of_stock,
            predicted_stockout_date=r.predicted_stockout_date,
            reorder_quantity=r.reorder_quantity,
            current_stock_snapshot=r.current_stock_snapshot,
            lead_time_snapshot=r.lead_time_snapshot,
            moq_snapshot=r.moq_snapshot,
            mape_score=r.mape_score,
            abc_rank=r.abc_rank,
            annual_gross_profit=r.annual_gross_profit,
            demand_sigma=r.demand_sigma or 0.0,
            computed_at=r.computed_at,
        )

@strawberry.type
class PipelineResultType:
    success: bool
    products_processed: int
    rows_written: int
    stockout_corrections: int
    outlier_corrections: int
    message: str

@strawberry.type
class PredictionRunResultType:
    success: bool
    products_processed: int
    message: str

@strawberry.type
class DashboardKPIType:
    total_products: int
    actual_stockouts: int
    urgent_alerts: int
    predicted_stockouts_30d: int
    message: str

@strawberry.type
class IngestionResult:
    success: bool
    message: str
    platform: str
    products_count: int
    sales_logs_count: int

@strawberry.type
class SyncResultType:
    success: bool
    products_created: int
    sales_logs_created: int
    message: str

@strawberry.type
class InvitationType:
    """Type Invitation GraphQL (SaaS)"""
    id: strawberry.ID
    email: str
    organization_id: strawberry.ID
    role: str
    status: str
    code: Optional[str] = None
    created_at: datetime
    expires_at: datetime

@strawberry.input
class LoginInput:
    """Input pour mutation login (SaaS)"""
    email: str
    password: str

@strawberry.input
class RegisterInput:
    """Input pour mutation register (Sprint 16)"""
    email: str
    password: str
    first_name: str
    last_name: str

@strawberry.input
class GoogleLoginInput:
    """Input pour authentification Google (SaaS)"""
    id_token: str

@strawberry.type
class TwoFactorSetupType:
    secret: str
    provisioning_uri: str

@strawberry.type
class TwoFactorConfirmResult:
    success: bool
    recovery_codes: Optional[List[str]] = None

@strawberry.type
class AuthPayload:
    """Payload retourné par login"""
    token: Optional[str] = None
    user: Optional[UserType] = None
    mfa_required: bool = False
    mfa_token: Optional[str] = None

@strawberry.input
class UpdateProfileInput:
    """Input pour modification profil (US 11.2)"""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email_alerts_enabled: Optional[bool] = None
    min_severity: Optional[int] = None

@strawberry.input
class UpdateOrganizationInput:
    """Input pour modification organisation (Sprint 16 Relocation)"""
    name: Optional[str] = None
    currency: Optional[str] = None
    is_mutualized: Optional[bool] = None
    report_enabled: Optional[bool] = None
    report_frequency: Optional[str] = None
    report_recipients: Optional[str] = None
    onboarding_completed: Optional[bool] = strawberry.field(default=None, name="onboardingCompleted")
    onboarding_step: Optional[str] = strawberry.field(default=None, name="onboardingStep")

@strawberry.input
class ChangePasswordInput:
    """Input pour modification de mot de passe"""
    current_password: str
    new_password: str

# SourceType alias for backward compatibility or refactor frontend
SourceType = StoreType

@strawberry.input
class RequestPasswordResetInput:
    email: str

@strawberry.input
class ResetPasswordInput:
    token: str
    new_password: str
@strawberry.type
class MappingSuggestionType:
    target_field: str
    csv_column: str
    confidence: float

@strawberry.type
class CsvAnalysisType:
    columns: List[str]
    column_types: str
    suggested_mapping: List[MappingSuggestionType]
    sample_data: str
    anomalies: str
    impact_summary: Optional[str] = None

@strawberry.input
class SmartImportInput:
    store_id: strawberry.ID
    csv_content: str
    mapping: str

@strawberry.type
class UserDataExportType:
    data_json: str
