"""
Schema GraphQL Principal
"""
import strawberry

from .types import User, LoginInput, AuthPayload
from src.modules.auth.service import AuthService
from src.modules.shopify.resolvers import ShopifyQuery, ShopifyMutation
from src.modules.forecasting.resolvers import ForecastingQuery, ForecastingMutation
from src.core.exceptions import UnauthenticatedException


@strawberry.type
class Query(ShopifyQuery, ForecastingQuery):
    """Queries GraphQL"""

    @strawberry.field
    async def me(self, info) -> User:
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

        return User(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            shop_id=strawberry.ID(str(user.shop_id)),
            created_at=user.created_at,
        )


@strawberry.type
class Mutation(ShopifyMutation, ForecastingMutation):
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

        return AuthPayload(
            token=result.token,
            user=User(
                id=strawberry.ID(str(result.user.id)),
                email=result.user.email,
                shop_id=strawberry.ID(str(result.user.shop_id)),
                created_at=result.user.created_at,
            ),
        )


# Schema final
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
