"""
Main GraphQL Schema — Sprint 21 Hexagonal Refactoring.
Pure composition of modular resolvers.
"""
import strawberry

# Auth & Organizations
from modules.auth import (
    AuthQuery, AuthMutation,
    OrgQuery, OrgMutation,
    InvitationQuery, InvitationMutation
)

# Inventory & Forecasting
from modules.inventory.adapters.resolvers import InventoryQuery, InventoryMutation
from modules.forecasting.adapters.resolvers import ForecastingQuery, ForecastingMutation

# Other Modules
from modules.shopify.adapters.resolvers import ShopifyQuery, ShopifyMutation
from modules.decisions.adapters.resolvers import DecisionQuery, DecisionMutation
from modules.billing.adapters.resolvers import BillingQuery, BillingMutation


@strawberry.type
class Query(
    AuthQuery, 
    OrgQuery, 
    InvitationQuery, 
    InventoryQuery, 
    ForecastingQuery, 
    DecisionQuery, 
    ShopifyQuery, 
    BillingQuery
):
    """Composition des Queries GraphQL de tous les modules."""
    pass


@strawberry.type
class Mutation(
    AuthMutation, 
    OrgMutation, 
    InvitationMutation, 
    InventoryMutation, 
    ForecastingMutation, 
    DecisionMutation, 
    ShopifyMutation, 
    BillingMutation
):
    """Composition des Mutations GraphQL de tous les modules."""
    pass


# Export du schéma final
schema = strawberry.Schema(query=Query, mutation=Mutation)
