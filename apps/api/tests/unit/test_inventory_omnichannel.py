import pytest
import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from modules.inventory.application.omnichannel_service import OmnichannelService
from modules.inventory.application.alert_service import AlertService
from modules.inventory.application.supplier_service import SupplierService
from modules.intelligence.algorithms.mape import calculate_mape_score

from modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
from modules.inventory.infrastructure.repositories.alert_repository import SQLAlchemyAlertRepository
from modules.inventory.infrastructure.repositories.supplier_repository import SQLAlchemySupplierRepository
from modules.inventory.infrastructure.repositories.purchase_order_repository import SQLAlchemyPurchaseOrderRepository
from modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository
from modules.auth.infrastructure.repositories import SQLAlchemyMembershipRepository, SQLAlchemyUserRepository

from modules.inventory.application.email_service import EmailService
from modules.inventory.domain.entities import PlatformSource
from modules.inventory.infrastructure.persistence.models import Product, PurchaseOrder, Supplier, Store
from modules.forecasting.infrastructure.persistence.models import Prediction

@pytest.fixture
async def test_store(db_session, test_user):
    """Fixture pour créer un store connecté pour les tests."""
    from modules.inventory.infrastructure.persistence.models import Store
    store = Store(
        id=uuid.uuid4(),
        organization_id=test_user.current_organization_id,
        name="Test Store",
        platform=PlatformSource.SHOPIFY,
        connected=True
    )
    db_session.add(store)
    await db_session.flush()
    return store

@pytest.mark.asyncio
async def test_omnichannel_aggregation(db_session, test_user, test_store):
    """Sprint 9 : Teste l'agrégation de produits par SKU sur plusieurs canaux."""
    org_id = test_user.current_organization_id
    shop_id = test_store.id
    
    # 1. Créer 2 produits avec le même SKU sur 2 plateformes
    p1 = Product(
        id=uuid.uuid4(), store_id=shop_id, sku="SKU-AGG-1", title="Prod Shopify",
        current_stock=10, source_platform=PlatformSource.SHOPIFY, lead_time=14, moq=1, stock_weight=1.0
    )
    p2 = Product(
        id=uuid.uuid4(), store_id=shop_id, sku="SKU-AGG-1", title="Prod Woo",
        current_stock=5, source_platform=PlatformSource.WOOCOMMERCE, lead_time=14, moq=1, stock_weight=1.0
    )
    db_session.add_all([p1, p2])
    await db_session.flush()

    # 2. Appeler le service omnichannel
    prod_repo = SQLAlchemyProductRepository(db_session)
    store_repo = SQLAlchemyStoreRepository(db_session)
    pred_repo = SQLAlchemyPredictionRepository(db_session)
    service = OmnichannelService(prod_repo, store_repo, pred_repo)
    items = await service.get_omnichannel_inventory(str(org_id))

    # 3. Vérifications
    assert len(items) >= 1
    omni_prod = next(item for item in items if item.sku == "SKU-AGG-1")
    assert omni_prod.total_stock == 15
    assert omni_prod.channel_count == 2

@pytest.mark.asyncio
async def test_omnichannel_csv_export(db_session, test_user, test_store):
    """Sprint 9 : Teste la génération du CSV de réapprovisionnement."""
    org_id = test_user.current_organization_id
    shop_id = test_store.id
    
    # Créer un produit avec prédiction
    p1 = Product(
        id=uuid.uuid4(), store_id=shop_id, sku="SKU-CSV-1", title="Prod CSV",
        current_stock=5, source_platform=PlatformSource.SHOPIFY, lead_time=14, moq=1, stock_weight=1.0
    )
    db_session.add(p1)
    await db_session.flush()
    
    pred = Prediction(
        id=uuid.uuid4(), product_id=p1.id,
        run_rate=2.0, reorder_quantity=50, abc_rank='A',
        predicted_stockout_date=date.today() + timedelta(days=2),
        current_stock_snapshot=5.0,
        lead_time_snapshot=14,
        moq_snapshot=1
    )
    db_session.add(pred)
    await db_session.flush()

    prod_repo = SQLAlchemyProductRepository(db_session)
    store_repo = SQLAlchemyStoreRepository(db_session)
    pred_repo = SQLAlchemyPredictionRepository(db_session)
    service = OmnichannelService(prod_repo, store_repo, pred_repo)
    
    csv_content = await service.generate_replenishment_csv(str(org_id))
    
    assert "SKU-CSV-1" in csv_content
    assert "Dominant Run Rate" in csv_content

@pytest.mark.asyncio
async def test_alert_service_dynamic_recipients(db_session, test_user, test_store):
    """Sprint 7 : Teste la génération d'alertes avec destinataires dynamiques."""
    shop_id = test_store.id
    
    # 1. Créer un produit en rupture (stock <= lead_time)
    product = Product(
        id=uuid.uuid4(), store_id=shop_id, sku="SKU-ALERT-7", title="Alerte Sprint 7",
        current_stock=2, lead_time=10, source_platform=PlatformSource.SHOPIFY,
        moq=1, stock_weight=1.0
    )
    db_session.add(product)
    await db_session.flush()

    # 2. Mocker EmailService
    mock_email_service = AsyncMock(spec=EmailService)
    mock_email_service.send_stockout_warning.return_value = True
    
    alert_repo = SQLAlchemyAlertRepository(db_session)
    prod_repo = SQLAlchemyProductRepository(db_session)
    store_repo = SQLAlchemyStoreRepository(db_session)
    membership_repo = SQLAlchemyMembershipRepository(db_session)
    user_repo = SQLAlchemyUserRepository(db_session)
    
    service = AlertService(
        alert_repo=alert_repo, 
        product_repo=prod_repo, 
        store_repo=store_repo, 
        membership_repo=membership_repo,
        user_repo=user_repo,
        email_service=mock_email_service
    )
    
    # 3. Lancer la vérification
    alerts = await service.check_for_stockouts(str(shop_id))

    # 4. Vérifier Alerte et Email
    assert len(alerts) > 0
    assert mock_email_service.send_stockout_warning.called
    
    # Vérifier que l'email a été envoyé au test_user
    args, _ = mock_email_service.send_stockout_warning.call_args
    # args[0] est to_email
    assert args[0] == test_user.email

@pytest.mark.asyncio
async def test_supplier_performance_calculation(db_session, test_user, test_store):
    """Sprint 8 : Teste le calcul du score de fiabilité fournisseur."""
    shop_id = test_store.id
    
    # 1. Créer un fournisseur
    supplier = Supplier(
        id=uuid.uuid4(), store_id=shop_id, name="Test Supplier",
        reliability_score=0.0, average_delay_days=0.0
    )
    db_session.add(supplier)
    await db_session.flush()

    # 2. Créer des Purchase Orders (un à l'heure, un en retard)
    po1 = PurchaseOrder(
        id=uuid.uuid4(), store_id=shop_id, product_id=uuid.uuid4(), supplier_id=supplier.id,
        quantity=100, order_date=date.today() - timedelta(days=20),
        expected_arrival_date=date.today() - timedelta(days=10),
        actual_arrival_date=date.today() - timedelta(days=10), # On time
        status="RECEIVED"
    )
    po2 = PurchaseOrder(
        id=uuid.uuid4(), store_id=shop_id, product_id=uuid.uuid4(), supplier_id=supplier.id,
        quantity=100, order_date=date.today() - timedelta(days=20),
        expected_arrival_date=date.today() - timedelta(days=10),
        actual_arrival_date=date.today() - timedelta(days=5), # 5 days late
        status="RECEIVED"
    )
    db_session.add_all([po1, po2])
    await db_session.flush()

    # 3. Calculer la performance
    supplier_repo = SQLAlchemySupplierRepository(db_session)
    po_repo = SQLAlchemyPurchaseOrderRepository(db_session)
    service = SupplierService(supplier_repo, po_repo)
    
    updated = await service.update_supplier_performance(supplier.id)
    
    # 4. Vérifier les scores
    assert updated.reliability_score == 0.5 # 1/2 à l'heure
    assert updated.average_delay_days == 2.5 # (0 + 5) / 2

@pytest.mark.asyncio
async def test_mape_accuracy_calculation():
    """Sprint 10 : Teste le calcul du score MAPE."""
    import pandas as pd
    
    # Case 1: Perfect prediction
    run_rate = 10.0
    sales = pd.Series([10.0, 10.0, 10.0])
    score = calculate_mape_score(run_rate, sales)
    assert score == 0.0
    
    # Case 2: 50% error
    run_rate = 15.0
    sales = pd.Series([10.0, 10.0, 10.0])
    score = calculate_mape_score(run_rate, sales)
    assert score == 0.5
