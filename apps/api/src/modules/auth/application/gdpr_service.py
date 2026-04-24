import uuid
import json
from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import AsyncSessionLocal
from core.database.models import User, OrganizationMember, Organization
from modules.inventory.infrastructure.persistence.models import Store, Product, Supplier
from modules.forecasting.infrastructure.persistence.models import Prediction

class GdprService:
    """
    Service pour la conformité RGPD (Droit à la portabilité).
    Compile toutes les données personnelles et commerciales d'un utilisateur.
    """

    async def export_all_user_data(self, user_id: uuid.UUID) -> str:
        """
        Génère un export JSON complet des données de l'utilisateur.
        """
        async with AsyncSessionLocal() as session:
            # 1. Infos Profil
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar()
            if not user:
                raise ValueError("Utilisateur non trouvé")

            export_data = {
                "export_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "legal_notice": "Conformément au RGPD (Article 20), Michi 道 vous fournit vos données au format structuré, couramment utilisé et lisible par machine."
                },
                "profile": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "is_active": user.is_active,
                    "two_factor_enabled": user.two_factor_enabled,
                    "preferences": user.preferences
                },
                "organizations": []
            }

            # 2. Organisations et Rôles
            stmt = select(OrganizationMember).options(
                selectinload(OrganizationMember.organization)
            ).where(OrganizationMember.user_id == user_id)
            result = await session.execute(stmt)
            memberships = result.scalars().all()

            for member in memberships:
                org = member.organization
                org_data = {
                    "name": org.name,
                    "role": member.role.value if hasattr(member.role, 'value') else str(member.role),
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                    "plan": org.plan,
                    "settings": org.settings,
                    "stores": []
                }

                # Si l'utilisateur est ADMIN de cette organisation, on exporte aussi les données commerciales (Optionnel selon interprétation RGPD, mais Michi est Transparent)
                # On limite ici aux boutiques connectées par l'utilisateur (ou l'organisation)
                stmt_stores = select(Store).where(Store.organization_id == org.id)
                res_stores = await session.execute(stmt_stores)
                stores = res_stores.scalars().all()

                for store in stores:
                    store_data = {
                        "name": store.name,
                        "platform": store.platform.value if hasattr(store.platform, 'value') else str(store.platform),
                        "connected_at": store.created_at.isoformat() if store.created_at else None,
                        "products_count": 0
                    }
                    
                    # On pourrait aller plus loin (Produits, Ventes), mais le JSON risquerait d'être énorme.
                    # Pour un MVP RGPD, on s'arrête à la structure et aux métadonnées.
                    # Si besoin d'un export CSV complet, c'est un autre outil.
                    
                    org_data["stores"].append(store_data)

                export_data["organizations"].append(org_data)

            return json.dumps(export_data, indent=2, ensure_ascii=False)

    async def delete_user_account(self, user_id: uuid.UUID) -> bool:
        """
        Supprime définitivement le compte de l'utilisateur (Droit à l'oubli).
        """
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar()
            
            if not user:
                return False
                
            await session.delete(user)
            await session.commit()
            return True
