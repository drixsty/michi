"""
Schema GraphQL Principal
"""
import strawberry
from typing import List

from .types import UserType, LoginInput, AuthPayload, UpdateProfileInput, ChangePasswordInput, SourceType
from src.modules.auth.service import AuthService
from src.modules.shopify.resolvers import ShopifyQuery, ShopifyMutation
from src.modules.forecasting.resolvers import ForecastingQuery, ForecastingMutation
from src.modules.inventory.resolvers import InventoryQuery, InventoryMutation
from src.core.exceptions import UnauthenticatedException


@strawberry.type
class Query(ShopifyQuery, ForecastingQuery, InventoryQuery):
    """Queries GraphQL"""

    @strawberry.field
    async def me(self, info) -> UserType:
        """
        Récupère l'utilisateur actuellement connecté.
        Nécessite authentication (JWT token).
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        auth_service = AuthService(info.context.db)
        user = await auth_service.get_user_by_id(info.context.user_id)

        if not user:
            raise UnauthenticatedException()

        import json
        return UserType(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            shop_id=strawberry.ID(str(user.shop_id)),
            created_at=user.created_at,
            preferences=json.dumps(user.preferences or {}),
        )

    @strawberry.field
    async def sources(self, info) -> List[SourceType]:
        """Retourne les sources de données disponibles et leur état."""
        return [
            SourceType(id=strawberry.ID("1"), name="Shopify", platform="shopify", connected=True),
            SourceType(id=strawberry.ID("2"), name="WooCommerce", platform="woocommerce", connected=False),
            SourceType(id=strawberry.ID("3"), name="Amazon", platform="amazon", connected=False),
        ]


@strawberry.type
class Mutation(ShopifyMutation, ForecastingMutation, InventoryMutation):
    """Mutations GraphQL"""

    @strawberry.mutation
    async def login(self, info, input: LoginInput) -> AuthPayload:
        """
        Authentifie un utilisateur et retourne un token JWT.

        Example:
            mutation {
              login(input: {email: "user@example.com", password: "password"}) {
                token
                user { id email }
              }
            }
        """
        auth_service = AuthService(info.context.db)

        from src.modules.auth.schemas import LoginInput as LoginInputSchema
        login_data = LoginInputSchema(email=input.email, password=input.password)

        result = await auth_service.login(login_data)

        import json
        return AuthPayload(
            token=result.token,
            user=UserType(
                id=strawberry.ID(str(result.user.id)),
                email=result.user.email,
                shop_id=strawberry.ID(str(result.user.shop_id)),
                created_at=result.user.created_at,
                preferences=json.dumps(result.user.preferences or {}),
            ),
        )

    @strawberry.mutation
    async def update_profile(self, info, input: UpdateProfileInput) -> UserType:
        """
        Met à jour le profil de l'utilisateur (US 11.2).
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        auth_service = AuthService(info.context.db)
        
        # Préférences extraites de l'input
        prefs = {}
        if input.email_alerts_enabled is not None:
            prefs["email_alerts_enabled"] = input.email_alerts_enabled
        if input.min_severity is not None:
            prefs["min_severity"] = input.min_severity
            
        user = await auth_service.update_user(
            user_id=info.context.user_id,
            email=input.email,
            preferences=prefs if prefs else None
        )

        import json
        return UserType(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            shop_id=strawberry.ID(str(user.shop_id)),
            created_at=user.created_at,
            preferences=json.dumps(user.preferences or {}),
        )

    @strawberry.mutation
    async def change_password(self, info, input: ChangePasswordInput) -> bool:
        """
        Change le mot de passe de l'utilisateur.
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        auth_service = AuthService(info.context.db)
        return await auth_service.change_password(
            user_id=info.context.user_id,
            current_password=input.current_password,
            new_password=input.new_password
        )

    @strawberry.mutation
    async def toggle_source(self, info, platform: str, connected: bool) -> SourceType:
        """Simule la connexion/déconnexion d'une source de données."""
        name_map = {"shopify": "Shopify", "woocommerce": "WooCommerce", "amazon": "Amazon"}
        return SourceType(
            id=strawberry.ID(f"src_{platform}"),
            name=name_map.get(platform, platform.capitalize()),
            platform=platform,
            connected=connected
        )


from .extensions import SQLAlchemySessionExtension

# Schema final
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[SQLAlchemySessionExtension],
)
