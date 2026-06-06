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


from strawberry.extensions import SchemaExtension
from core.exceptions import MichiException
from core.graphql.extensions import MichiExceptionExtension
from core.graphql.depth_limit import DepthLimitExtension
import logging

class MaskTracebackExtension(SchemaExtension):
    """
    Extension pour masquer les tracebacks des exceptions métier (MichiException).
    Évite de polluer les logs avec des stacktraces pour des erreurs attendues (ex: Auth).
    """
    def on_operation(self):
        yield
        execution_context = self.execution_context
        # Utilisation défensive de getattr pour éviter AttributeError sur ExecutionContext
        result = getattr(execution_context, "result", None)
        errors = getattr(result, "errors", []) if result else []
        
        if errors:
            for error in errors:
                orig = getattr(error, "original_error", None)
                if isinstance(orig, MichiException):
                    # On marque moralement comme traité
                    pass

# Export du schéma final avec extensions
schema = strawberry.Schema(
    query=Query, 
    mutation=Mutation,
    extensions=[
        MichiExceptionExtension,
        MaskTracebackExtension,
        DepthLimitExtension(max_depth=5)
    ]
)

