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
from src.modules.decisions.resolvers import DecisionQuery, DecisionMutation
from src.core.exceptions import UnauthenticatedException


@strawberry.type
class Query(ShopifyQuery, ForecastingQuery, InventoryQuery, DecisionQuery):
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
        """Retourne les sources de données disponibles et leur état (Sprint 17)."""
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        from src.modules.auth.service import AuthService
        from src.modules.inventory.models import SourceConnection, PlatformSource
        from sqlalchemy import select
        
        user = await AuthService(info.context.db).get_user_by_id(info.context.user_id)
        shop_id = user.shop_id
        
        # 1. Récupérer les connexions existantes
        result = await info.context.db.execute(
            select(SourceConnection).where(SourceConnection.shop_id == shop_id)
        )
        found_connections = {c.platform: c for c in result.scalars().all()}
        
        # 2. S'assurer que les 3 plateformes par défaut sont présentes (Seed à la volée)
        default_platforms = [PlatformSource.SHOPIFY, PlatformSource.WOOCOMMERCE, PlatformSource.AMAZON]
        name_map = {"shopify": "Shopify", "woocommerce": "WooCommerce", "amazon": "Amazon"}
        
        all_sources = []
        for p in default_platforms:
            conn = found_connections.get(p)
            if not conn:
                # Création automatique de la source inactive
                conn = SourceConnection(
                    shop_id=shop_id,
                    platform=p,
                    connected=False
                )
                info.context.db.add(conn)
                await info.context.db.flush()
            
            all_sources.append(
                SourceType(
                    id=strawberry.ID(str(conn.id)),
                    name=name_map.get(p.value, p.value.capitalize()),
                    platform=p.value,
                    connected=conn.connected,
                    last_sync_at=conn.last_sync_at,
                    health_status=conn.health_status
                )
            )
        
        await info.context.db.commit()
        return all_sources


@strawberry.type
class Mutation(ShopifyMutation, ForecastingMutation, InventoryMutation, DecisionMutation):
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
        if input.currency is not None:
            prefs["currency"] = input.currency
        if input.is_mutualized is not None:
            prefs["is_mutualized"] = input.is_mutualized
            
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

    @strawberry.mutation(name="toggleSource")
    async def toggle_source(self, info, platform: str, connected: bool) -> SourceType:
        """Gestion réelle du cycle de vie d'une source (Sprint 17)."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        from src.modules.auth.service import AuthService
        from src.modules.inventory.models import SourceConnection, PlatformSource, Product, SalesLog, Alert
        from src.modules.forecasting.models import Prediction
        from sqlalchemy import select, delete
        from datetime import datetime
        
        user = await AuthService(info.context.db).get_user_by_id(info.context.user_id)
        shop_id = user.shop_id
        
        # 1. Récupérer ou créer la connexion
        plat_enum = PlatformSource(platform)
        result = await info.context.db.execute(
            select(SourceConnection).where(
                SourceConnection.shop_id == shop_id,
                SourceConnection.platform == plat_enum
            )
        )
        conn = result.scalar_one_or_none()
        
        if not conn:
            conn = SourceConnection(shop_id=shop_id, platform=plat_enum)
            info.context.db.add(conn)
            
        conn.connected = connected
        
        # 2. Logique destructive ou synchronisation
        if not connected:
            # DÉCONNEXION : Supprimer toutes les données liées à cette source
            # On récupère les IDs des produits pour supprimer les SalesLogs/Alerts/Predictions
            # (Note: cascade=all, delete-orphan dans les modèles devrait gérer cela, 
            # mais on le fait explicitement par sécurité pour la plateforme cible)
            
            # Suppression des produits de cette plateforme pour cette boutique
            # La cascade SQL/SQLAlchemy via relationship(cascade="all, delete-orphan") fera le reste
            await info.context.db.execute(
                delete(Product).where(
                    Product.shop_id == shop_id,
                    Product.source_platform == plat_enum
                )
            )
        else:
            # CONNEXION : Déclenchement automatique de la synchronisation (Mock/Real)
            conn.last_sync_at = datetime.utcnow()
            conn.health_status = "HEALTHY"
            
            from src.modules.inventory.resolvers import InventoryMutation
            # On appelle le trigger de sync interne (serait idéalement un service)
            # await InventoryMutation().trigger_omnichannel_sync(info)
            # Pour l'instant on simule l'appel au service global qui sera implémenté en phase 3
            
        await info.context.db.commit()
        
        name_map = {"shopify": "Shopify", "woocommerce": "WooCommerce", "amazon": "Amazon"}
        return SourceType(
            id=strawberry.ID(str(conn.id)),
            name=name_map.get(platform, platform.capitalize()),
            platform=platform,
            connected=conn.connected,
            last_sync_at=conn.last_sync_at,
            health_status=conn.health_status
        )


from .extensions import SQLAlchemySessionExtension

# Schema final
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[SQLAlchemySessionExtension],
)
