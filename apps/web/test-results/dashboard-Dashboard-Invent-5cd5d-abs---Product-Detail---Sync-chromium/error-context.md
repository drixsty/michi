# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.ts >> Dashboard & Inventory Full Journey >> Complete Dashboard Journey: Registration -> Onboarding -> Tabs -> Product Detail -> Sync
- Location: e2e\dashboard.spec.ts:23:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="inventory-title"]')
Expected: visible
Timeout: 15000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 15000ms
  - waiting for locator('[data-testid="inventory-title"]')

```

# Page snapshot

```yaml
- dialog "Unhandled Runtime Error" [ref=e3]:
  - generic [ref=e4]:
    - generic [ref=e5]:
      - generic [ref=e6]:
        - navigation [ref=e7]:
          - button "previous" [disabled] [ref=e8]:
            - img "previous" [ref=e9]
          - button "next" [disabled] [ref=e11]:
            - img "next" [ref=e12]
          - generic [ref=e14]: 1 of 1 unhandled error
          - generic [ref=e15]:
            - text: Next.js (14.1.0) is outdated
            - link "(learn more)" [ref=e17] [cursor=pointer]:
              - /url: https://nextjs.org/docs/messages/version-staleness
        - button "Close" [ref=e18] [cursor=pointer]:
          - img [ref=e20]
      - heading "Unhandled Runtime Error" [level=1] [ref=e23]
      - paragraph [ref=e24]: "ReferenceError: useMemo is not defined"
    - generic [ref=e25]:
      - heading "Source" [level=2] [ref=e26]
      - generic [ref=e27]:
        - link "src\\components\\dashboard\\ProductTable.tsx (92:29) @ useMemo" [ref=e29] [cursor=pointer]:
          - generic [ref=e30]: src\components\dashboard\ProductTable.tsx (92:29) @ useMemo
          - img [ref=e31]
        - generic [ref=e35]: "90 | }, [products, query, channelFilter]); 91 | > 92 | const availablePlatforms = useMemo(() => { | ^ 93 | const platforms = new Set<string>(); 94 | products.forEach(p => { 95 | (p.channels || []).forEach((c: any) => platforms.add(c.platform.toLowerCase()));"
      - button "Show collapsed frames" [ref=e36] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import { AuthPage } from './pages/AuthPage';
  3  | import { OnboardingPage } from './pages/OnboardingPage';
  4  | import { DashboardPage } from './pages/DashboardPage';
  5  | 
  6  | /**
  7  |  * US 21.23 - Validation E2E Dashboard & Inventaire
  8  |  * On utilise une seule session de test longue pour valider l'enchaînement complet
  9  |  * et éviter de perdre la session (localStorage) entre les tests atomiques.
  10 |  */
  11 | test.describe('Dashboard & Inventory Full Journey', () => {
  12 |   let authPage: AuthPage;
  13 |   let onboardingPage: OnboardingPage;
  14 |   let dashboardPage: DashboardPage;
  15 |   
  16 |   const testUser = {
  17 |     email: `dash-full-${Math.floor(Math.random() * 10000)}@michi.com`,
  18 |     password: 'Password123!',
  19 |     firstName: 'Dash',
  20 |     lastName: 'Runner'
  21 |   };
  22 | 
  23 |   test('Complete Dashboard Journey: Registration -> Onboarding -> Tabs -> Product Detail -> Sync', async ({ page }) => {
  24 |     authPage = new AuthPage(page);
  25 |     onboardingPage = new OnboardingPage(page);
  26 |     dashboardPage = new DashboardPage(page);
  27 | 
  28 |     // 1. Registration
  29 |     await authPage.gotoRegister();
  30 |     await authPage.register(testUser.firstName, testUser.lastName, testUser.email, testUser.password);
  31 |     
  32 |     // 2. Onboarding
  33 |     await onboardingPage.completeWizard();
  34 |     await dashboardPage.expectLoggedIn();
  35 | 
  36 |     // 3. Tab Navigation
  37 |     // Overview (Default)
  38 |     await expect(page.locator('text=Tableau de bord')).toBeVisible();
  39 |     await expect(page.locator('text=Alertes récentes')).toBeVisible();
  40 | 
  41 |     // Inventory
  42 |     await dashboardPage.switchTab('inventory');
  43 |     // Wait for the inventory title (longer timeout for the first query)
> 44 |     await expect(page.locator('[data-testid="inventory-title"]')).toBeVisible({ timeout: 15000 });
     |                                                                   ^ Error: expect(locator).toBeVisible() failed
  45 | 
  46 |     // 4. Sync & Search
  47 |     await dashboardPage.triggerSync();
  48 |     await dashboardPage.searchProduct('Test');
  49 |     
  50 |     // 5. Product QuickView
  51 |     // On clique sur le premier produit trouvé (ou "Données vides" si sync mock est lent, 
  52 |     // mais triggerSync attend le message de succès)
  53 |     const firstRow = page.locator('tbody tr').first();
  54 |     await firstRow.click();
  55 |     
  56 |     await expect(page.locator('[data-testid="product-quickview"]')).toBeVisible();
  57 |     await expect(page.locator('text=Simulateur What-if')).toBeVisible();
  58 |     
  59 |     // Test Simulator
  60 |     const slider = page.locator('input[type="range"]').first();
  61 |     await slider.fill('10'); // +10 jours
  62 |     await expect(page.locator('text=Simulation active')).toBeVisible();
  63 |     
  64 |     // Copy SKU (Vérification micro-interaction)
  65 |     await page.click('button[title="Copier le SKU"]');
  66 |     
  67 |     await page.click('[data-testid="close-quickview"]');
  68 |     await expect(page.locator('[data-testid="product-quickview"]')).not.toBeVisible();
  69 | 
  70 |     // 6. Decisions Tab
  71 |     await dashboardPage.switchTab('decisions');
  72 |     await expect(page.locator('text=Centre de Décision')).toBeVisible();
  73 |     await expect(page.locator('text=Capital immobilisé')).toBeVisible();
  74 |     await expect(page.locator('text=Risques financiers')).toBeVisible();
  75 | 
  76 |     // 7. Sources Tab
  77 |     await dashboardPage.switchTab('sources');
  78 |     await expect(page.locator('text=Navigation des sources')).toBeVisible();
  79 |     await expect(page.locator('text=Flux Automatiques')).toBeVisible();
  80 |   });
  81 | });
  82 | 
```