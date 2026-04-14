import { test, expect } from '@playwright/test';
import { AuthPage } from './pages/AuthPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { DashboardPage } from './pages/DashboardPage';

/**
 * US 21.23 - Validation E2E Dashboard & Inventaire
 * On utilise une seule session de test longue pour valider l'enchaînement complet
 * et éviter de perdre la session (localStorage) entre les tests atomiques.
 */
test.describe('Dashboard & Inventory Full Journey', () => {
  let authPage: AuthPage;
  let onboardingPage: OnboardingPage;
  let dashboardPage: DashboardPage;
  
  const testUser = {
    email: `dash-full-${Math.floor(Math.random() * 10000)}@michi.com`,
    password: 'Password123!',
    firstName: 'Dash',
    lastName: 'Runner'
  };

  test('Complete Dashboard Journey: Registration -> Onboarding -> Tabs -> Product Detail -> Sync', async ({ page }) => {
    authPage = new AuthPage(page);
    onboardingPage = new OnboardingPage(page);
    dashboardPage = new DashboardPage(page);

    // 1. Registration
    await authPage.gotoRegister();
    await authPage.register(testUser.firstName, testUser.lastName, testUser.email, testUser.password);
    
    // 2. Onboarding
    await onboardingPage.completeWizard();
    await dashboardPage.expectLoggedIn();

    // 3. Tab Navigation
    // Overview (Default)
    await expect(page.locator('text=Tableau de bord')).toBeVisible();
    await expect(page.locator('text=Alertes récentes')).toBeVisible();

    // Inventory
    await dashboardPage.switchTab('inventory');
    // Wait for the inventory title (longer timeout for the first query)
    await expect(page.locator('[data-testid="inventory-title"]')).toBeVisible({ timeout: 15000 });

    // 4. Sync & Search
    await dashboardPage.triggerSync();
    await dashboardPage.searchProduct('Test');
    
    // 5. Product QuickView
    // On clique sur le premier produit trouvé (ou "Données vides" si sync mock est lent, 
    // mais triggerSync attend le message de succès)
    const firstRow = page.locator('tbody tr').first();
    await firstRow.click();
    
    await expect(page.locator('[data-testid="product-quickview"]')).toBeVisible();
    await expect(page.locator('text=Simulateur What-if')).toBeVisible();
    
    // Test Simulator
    const slider = page.locator('input[type="range"]').first();
    await slider.fill('10'); // +10 jours
    await expect(page.locator('text=Simulation active')).toBeVisible();
    
    // Copy SKU (Vérification micro-interaction)
    await page.click('button[title="Copier le SKU"]');
    
    await page.click('[data-testid="close-quickview"]');
    await expect(page.locator('[data-testid="product-quickview"]')).not.toBeVisible();

    // 6. Decisions Tab
    await dashboardPage.switchTab('decisions');
    await expect(page.locator('text=Centre de Décision')).toBeVisible();
    await expect(page.locator('text=Capital immobilisé')).toBeVisible();
    await expect(page.locator('text=Risques financiers')).toBeVisible();

    // 7. Sources Tab
    await dashboardPage.switchTab('sources');
    await expect(page.locator('text=Navigation des sources')).toBeVisible();
    await expect(page.locator('text=Flux Automatiques')).toBeVisible();
  });
});
