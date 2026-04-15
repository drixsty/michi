"""
Types GraphQL avec Strawberry
"""
import strawberry
from typing import Optional, List
from datetime import datetime, date

@strawberry.type
class OrganizationType:
    """Type Organization GraphQL"""
    id: strawberry.ID
    name: str
    slug: str
    plan: str
    subscription_status: str
    created_at: datetime
    settings: str # Keep as JSON string for now to avoid frontend breaking, but centralize mapping

    @classmethod
    def from_db(cls, org):
        import json
        return cls(
            id=strawberry.ID(str(org.id)),
            name=org.name,
            slug=org.slug,
            plan=org.plan,
            subscription_status=org.subscription_status,
            created_at=org.created_at,
            settings=json.dumps(org.settings or {})
        )

@strawberry.type
class OrganizationMemberType:
    """Type OrganizationMember GraphQL (Liaison User/Org)"""
    organization_id: strawberry.ID
    user_id: strawberry.ID
    role: str
    permissions: str # JSON string
    organization: Optional[OrganizationType] = None
    user: Optional['UserType'] = None

    @classmethod
    def from_db(cls, member, include_org=True, include_user=False):
        import json
        
        # Determine role string
        role_val = member.role
        if hasattr(role_val, 'value'):
            role_val = role_val.value
            
        return cls(
            organization_id=strawberry.ID(str(member.organization_id)),
            user_id=strawberry.ID(str(member.user_id)),
            role=str(role_val),
            permissions=json.dumps(member.permissions or {}),
            organization=OrganizationType.from_db(member.organization) if (include_org and getattr(member, 'organization', None)) else None,
            user=UserType.from_db(member.user, include_orgs=False) if (include_user and getattr(member, 'user', None)) else None
        )

@strawberry.type
class UserType:
    """Type User GraphQL (SaaS Version)"""
    id: strawberry.ID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    current_organization_id: Optional[strawberry.ID] = None
    shop_id: Optional[strawberry.ID] = None
    created_at: datetime
    preferences: str
    
    # List of organizations the user belongs to
    organizations: List[OrganizationMemberType]

    @classmethod
    def from_db(cls, user, include_orgs=True):
        import json
        if not user: return None
        
        # Handle dict preferences vs object
        prefs = user.preferences
        if isinstance(prefs, dict):
            prefs_str = json.dumps(prefs)
        elif isinstance(prefs, str):
            prefs_str = prefs
        else:
            prefs_str = json.dumps(prefs or {})

        return cls(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            current_organization_id=strawberry.ID(str(user.current_organization_id)) if user.current_organization_id else None,
            shop_id=strawberry.ID(str(user.shop_id)) if getattr(user, 'shop_id', None) else None,
            created_at=user.created_at,
            preferences=prefs_str,
            organizations=[
                OrganizationMemberType.from_db(m) for m in getattr(user, 'organizations', [])
            ] if include_orgs else []
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

    @classmethod
    def from_db(cls, supplier):
        if not supplier: return None
        return cls(
            id=strawberry.ID(str(supplier.id)),
            name=supplier.name,
            contact_email=supplier.contact_email,
            reliability_score=supplier.reliability_score,
            average_delay_days=supplier.average_delay_days
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
        from src.modules.forecasting.adapters.resolvers import resolve_cleaned_demands
        return await resolve_cleaned_demands(info, str(self.id), self.sku)

    @strawberry.field
    async def channels(self, info) -> List["ChannelBreakdownType"]:
        from src.modules.inventory.adapters.resolvers import resolve_product_channels
        return await resolve_product_channels(info, self.sku)

    @strawberry.field
    async def prediction(self, info) -> Optional[Annotated["PredictionType", strawberry.lazy("src.modules.forecasting.adapters.resolvers")]]:
        from src.modules.forecasting.adapters.resolvers import resolve_product_prediction
        return await resolve_product_prediction(info, str(self.id), self.sku)

    @strawberry.field
    async def supplier(self, info) -> Optional[SupplierType]:
        if not self.supplier_id: return None
        from src.modules.inventory.adapters.resolvers import resolve_product_supplier
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
    def from_db(cls, r):
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
class AuthPayload:
    """Payload retourné par login"""
    token: str
    user: UserType

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

@strawberry.input
class ChangePasswordInput:
    """Input pour modification de mot de passe"""
    current_password: str
    new_password: str

# SourceType alias for backward compatibility or refactor frontend
SourceType = StoreType
