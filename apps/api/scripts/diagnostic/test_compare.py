import asyncio
from src.core.database import AsyncSessionLocal
from src.modules.decisions.service import DecisionCenterService

async def test_global_vs_shopify():
    async with AsyncSessionLocal() as db:
        user_id = '52aa6923-ffe9-4859-8589-1e84ba6a54a9'
        service = DecisionCenterService(db)
        
        print("--- Testing Global Overview ---")
        overview_all = await service.get_overview(user_id, store_id=None, channel=None)
        print(f"Global Risks Count: {len(overview_all.top_risks)}")
        print(f"Global Total Stock: {overview_all.total_stock}")
        
        shopify_id = '79e78f52-d206-4a9f-b6d2-87883fb6dd8a'
        print("\n--- Testing Shopify Only Overview ---")
        overview_shopify = await service.get_overview(user_id, store_id=shopify_id, channel=None)
        print(f"Shopify Risks Count: {len(overview_shopify.top_risks)}")
        print(f"Shopify Total Stock: {overview_shopify.total_stock}")
        
        amazon_id = '9714d233-c56f-48a1-972a-6b9d7efd73fb'
        print("\n--- Testing Amazon Only Overview ---")
        overview_amazon = await service.get_overview(user_id, store_id=amazon_id, channel=None)
        print(f"Amazon Risks Count: {len(overview_amazon.top_risks)}")
        print(f"Amazon Total Stock: {overview_amazon.total_stock}")

if __name__ == "__main__":
    asyncio.run(test_global_vs_shopify())
