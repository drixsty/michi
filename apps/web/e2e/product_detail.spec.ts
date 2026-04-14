import { test, expect } from '@playwright/test';
import { AuthPage } from './pages/AuthPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { DashboardPage } from './pages/DashboardPage';

test.describe('Product Detail & Inline Editing', () => {
  let authPage: AuthPage;
  let onboardingPage: OnboardingPage;
  let dashboardPage: DashboardPage;
  
  const testUser = {
    email: `prod-detail-${Math.floor(Math.random() * 10000)}@michi.com`,
    password: 'Password123!',
    firstName: 'Detail',
    lastName: 'Tester'
  };

  test('Navigate to Product Page and Edit Parameters', async ({ page }) => {
    authPage = new AuthPage(page);
    onboardingPage = new OnboardingPage(page);
    dashboardPage = new DashboardPage(page);

    // 1. Setup session
    await authPage.gotoRegister();
    await authPage.register(testUser.firstName, testUser.lastName, testUser.email, testUser.password);
    await onboardingPage.completeWizard();
    await dashboardPage.expectLoggedIn();

    // 2. Trigger sync to have data
    await dashboardPage.switchTab('inventory');
    await dashboardPage.triggerSync();

    // 3. Navigate to Product Detail
    // We click the first SKU link in the table
    const firstProductSku = page.locator('tbody tr td:nth-child(2)').first();
    const sku = await firstProductSku.innerText();
    await firstProductSku.click();

    // Verify QuickView first
    await expect(page.locator('[data-testid="product-quickview"]')).toBeVisible();
    
    // Go to Full Detail Page
    await page.click('[data-testid="open-full-detail"]');
    await expect(page).toHaveURL(/\/dashboard\/product\/.*/);
    await expect(page.locator('[data-testid="product-detail-view"]')).toBeVisible();

    // 4. Edit Parameters
    const leadTimeInput = page.locator('[data-testid="edit-lead-time"]');
    await leadTimeInput.fill('25');
    await leadTimeInput.blur(); // Trigger save
    
    await expect(page.locator('text=Paramètre mis à jour')).toBeVisible();

    // 5. Verify Charts
    await expect(page.locator('.recharts-surface')).toHaveCount(2); // Sales and Predictions
  });
});
