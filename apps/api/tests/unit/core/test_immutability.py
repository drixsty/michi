import pytest
from uuid import uuid4
from dataclasses import FrozenInstanceError
from modules.inventory.domain.entities import ProductEntity, PlatformSource

def test_product_entity_is_frozen():
    product = ProductEntity(
        id=uuid4(),
        store_id=uuid4(),
        sku="TEST-SKU",
        title="Original Title"
    )
    
    # Tenter de modifier un attribut doit lever une FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        product.title = "New Title" # type: ignore

def test_product_entity_cloning():
    product = ProductEntity(
        id=uuid4(),
        store_id=uuid4(),
        sku="TEST-SKU",
        title="Original Title"
    )
    
    # Pour modifier, on doit utiliser dataclasses.replace (clonage)
    from dataclasses import replace
    new_product = replace(product, title="New Title")
    
    assert new_product.title == "New Title"
    assert product.title == "Original Title" # L'original n'a pas bougé
    assert new_product.id == product.id # Les autres champs sont conservés
