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
import logging

class MaskTracebackExtension(SchemaExtension):
    """
    Extension pour masquer les tracebacks des exceptions métier (MichiException).
    Évite de polluer les logs avec des stacktraces pour des erreurs attendues (ex: Auth).
    """
    def on_operation(self):
        yield
        execution_context = self.execution_context
        if execution_context.errors:
            # On parcourt les erreurs pour détecter nos exceptions métier
            new_errors = []
            for error in execution_context.errors:
                orig = error.original_error
                if isinstance(orig, MichiException):
                    # On logue une version propre si on veut, mais Strawberry va quand même 
                    # stocker l'erreur dans execution_context.errors.
                    # Le but ici est surtout de marquer l'erreur comme 'traitée' moralement
                    # ou de préparer le terrain pour main.py.
                    pass
                new_errors.append(error)

# Export du schéma final avec extensions
schema = strawberry.Schema(
    query=Query, 
    mutation=Mutation,
    extensions=[MaskTracebackExtension]
)
