import pytest
import uuid
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.modules.inventory.application.omnichannel_service import OmnichannelService
from src.modules.inventory.application.alert_service import AlertService
from src.modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from src.modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
from src.modules.inventory.infrastructure.repositories.alert_repository import SQLAlchemyAlertRepository
from src.modules.inventory.application.email_service import EmailService
from src.modules.inventory.domain.entities import PlatformSource
from src.modules.inventory.infrastructure.persistence.models import Product, Alert, AlertEmail
from src.modules.forecasting.infrastructure.persistence.models import Prediction

@pytest.mark.asyncio
async def test_omnichannel_aggregation(db_session, test_user):
    """US 9.1 / 10.5 : Teste l'agrégation de produits par SKU sur plusieurs canaux."""
    shop_id = test_user.shop_id
    
    # 1. Créer 2 produits avec le même SKU sur 2 plateformes
    p1 = Product(
        id=uuid.uuid4(), store_id=shop_id, sku="SKU-AGG-1", title="Prod Shopify",
        current_stock=10, source_platform=PlatformSource.SHOPIFY
    )
    p2 = Product(
        id=uuid.uuid4(), store_id=shop_id, sku="SKU-AGG-1", title="Prod Woo",
        current_stock=5, source_platform=PlatformSource.WOOCOMMERCE
    )
    db_session.add_all([p1, p2])
    await db_session.commit()

    # 2. Appeler le service omnichannel
    prod_repo = SQLAlchemyProductRepository(db_session)
    store_repo = SQLAlchemyStoreRepository(db_session)
    service = OmnichannelService(prod_repo, store_repo)
    items = await service.get_omnichannel_inventory(str(test_user.current_organization_id))

    # 3. Vérifications
    assert len(items) == 1
    assert items[0].sku == "SKU-AGG-1"
    assert items[0].total_stock == 15
    assert items[0].channel_count == 2
    assert len(items[0].channels) == 2

@pytest.mark.asyncio
async def test_alert_service_ui_and_email(db_session, test_user):
    """US 10.5 / 10.4 : Teste la génération d'alertes UI et l'envoi d'emails avec anti-spam."""
    shop_id = test_user.shop_id
    
    # 1. Créer un produit en rupture imminente
    product = Product(
        id=uuid.uuid4(), store_id=shop_id, sku="SKU-ALERT-1", title="Alerte Prod",
        current_stock=5, lead_time=7, source_platform=PlatformSource.SHOPIFY
    )
    db_session.add(product)
    await db_session.flush()

    # Prédiction : rupture dans 2 jours (donc <= lead_time + 2)
    prediction = Prediction(
        id=uuid.uuid4(),
        product_id=product.id,
        run_rate=2.0,
        predicted_stockout_date=date.today() + timedelta(days=2),
        current_stock_snapshot=5, 
        lead_time_snapshot=7,
        moq_snapshot=1
    )
    db_session.add(prediction)
    await db_session.commit()

    # 2. Mocker EmailService
    with patch("src.modules.inventory.application.email_service.EmailService.send_stockout_warning", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        alert_repo = SQLAlchemyAlertRepository(db_session)
        prod_repo = SQLAlchemyProductRepository(db_session)
        store_repo = SQLAlchemyStoreRepository(db_session)
        
        service = AlertService(alert_repo, prod_repo, store_repo, EmailService())
        alerts = await service.check_for_stockouts(str(shop_id))

        # 3. Vérifier Alerte UI
        assert len(alerts) > 0
        assert any(a.type == "STOCKOUT_RISK_HIGH" for a in alerts)

        # 4. Vérifier Email envoyé
        assert mock_send.called
        
        # 5. Vérifier Anti-spam (ne pas renvoyer de suite)
        mock_send.reset_mock()
        await service.check_for_stockouts(str(shop_id))
        assert not mock_send.called  # Devrait être bloqué par AlertEmail logs


