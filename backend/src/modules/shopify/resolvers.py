"""
Resolvers GraphQL — Shopify
Types Strawberry + Query/Mutation pour produits, sync mock et validation.
"""
import strawberry
from typing import List
from datetime import datetime

from src.core.exceptions import UnauthenticatedException
from .service import ShopifyService
from .validation import DataValidationService


# ── Strawberry Types ──────────────────────────────────────────────────────────

@strawberry.type
class ProductType:
    id: strawberry.ID
    shop_id: strawberry.ID
    sku: str
    title: str
    current_stock: int
    lead_time: int
    moq: int
    created_at: datetime


@strawberry.type
class SyncResultType:
    success: bool
    products_created: int
    sales_logs_created: int
    message: str


@strawberry.type
class ValidationIssueType:
    rule: str
    severity: str
    detail: str


@strawberry.type
class ValidationReportType:
    is_valid: bool
    product_count: int
    sales_log_count: int
    stockout_ratio: float
    issues: List[ValidationIssueType]
    summary: str


# ── Query Extension ───────────────────────────────────────────────────────────

@strawberry.type
class ShopifyQuery:
    @strawberry.field
    async def products(self, info) -> List[ProductType]:
        """
        Retourne tous les produits du shop connecté.
        Nécessite authentication (JWT).

        Example:
            query {
              products {
                id sku title currentStock leadTime moq
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ShopifyService(info.context.db)
        items = await service.get_products(info.context.shop_id)

        return [
            ProductType(
                id=strawberry.ID(str(p.id)),
                shop_id=strawberry.ID(str(p.shop_id)),
                sku=p.sku,
                title=p.title,
                current_stock=p.current_stock,
                lead_time=p.lead_time,
                moq=p.moq,
                created_at=p.created_at,
            )
            for p in items
        ]

    @strawberry.field
    async def validate_mock_data(self, info) -> ValidationReportType:
        """
        Valide la cohérence du dataset mock (R1–R6).
        Nécessite authentication (JWT).

        Example:
            query {
              validateMockData {
                isValid productCount salesLogCount stockoutRatio summary
                issues { rule severity detail }
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        validator = DataValidationService(info.context.db)
        report = await validator.validate(info.context.shop_id)

        return ValidationReportType(
            is_valid=report.is_valid,
            product_count=report.product_count,
            sales_log_count=report.sales_log_count,
            stockout_ratio=report.stockout_ratio,
            issues=[
                ValidationIssueType(rule=i.rule, severity=i.severity, detail=i.detail)
                for i in report.issues
            ],
            summary=report.summary,
        )


# ── Mutation Extension ────────────────────────────────────────────────────────

@strawberry.type
class ShopifyMutation:
    @strawberry.mutation
    async def trigger_mock_data_sync(self, info) -> SyncResultType:
        """
        Régénère un dataset mock complet (50 produits + 365j historique).
        Nécessite authentication (JWT).

        Example:
            mutation {
              triggerMockDataSync {
                success productsCreated salesLogsCreated message
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ShopifyService(info.context.db)
        result = await service.trigger_mock_sync(info.context.shop_id)

        return SyncResultType(
            success=result.success,
            products_created=result.products_created,
            sales_logs_created=result.sales_logs_created,
            message=result.message,
        )
