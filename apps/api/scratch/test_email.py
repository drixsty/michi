import asyncio
from modules.inventory.application.email_service import EmailService

async def main():
    email_service = EmailService()
    print("Sending test stockout warning email...")
    res = await email_service.send_stockout_warning(
        to_email="dev@michi.com",
        product_title="Super Premium Matcha Tea",
        days_left=3
    )
    print(f"Result: {res}")

    print("Sending test purchase order email...")
    res_po = await email_service.send_purchase_order(
        to_email="supplier@premiummatcha.com",
        po_id="PO-2026-0001",
        supplier_name="Premium Matcha Ltd",
        product_title="Super Premium Matcha Tea",
        product_sku="MATCHA-PREM-500",
        quantity=150,
        order_date="2026-05-26",
        expected_date="2026-06-05"
    )
    print(f"PO Result: {res_po}")

    print("Sending test verification email...")
    res_verify = await email_service.send_verification_email(
        to_email="newuser@michi.com",
        verification_link="http://localhost:3000/verify-email?token=abc123xyz"
    )
    print(f"Verification Result: {res_verify}")

if __name__ == "__main__":
    asyncio.run(main())
