# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Authentication & Onboarding Flow >> 1. Full Registration and Onboarding Flow
- Location: tests\e2e\auth.spec.ts:34:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="wizard-platform-csv"]')
Expected: visible
Timeout: 15000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 15000ms
  - waiting for locator('[data-testid="wizard-platform-csv"]')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e2]:
    - img "background" [ref=e4]
    - generic [ref=e6]:
      - generic [ref=e7]:
        - generic [ref=e8]:
          - generic [ref=e9]:
            - generic [ref=e10]: 道
            - generic [ref=e11]: Michi
          - generic [ref=e12]:
            - heading "Initialisez votre espace." [level=2] [ref=e13]
            - paragraph [ref=e14]: Connectez vos sources de données et laissez notre IA optimiser vos stocks.
        - generic [ref=e16]:
          - generic [ref=e18]:
            - generic [ref=e19]: "1"
            - generic [ref=e20]:
              - generic [ref=e21]: Identité
              - generic [ref=e22]: Nom de l'espace
          - generic [ref=e23]:
            - generic [ref=e24]: "2"
            - generic [ref=e25]:
              - generic [ref=e26]: Forfait
              - generic [ref=e27]: Capacité de calcul
      - generic [ref=e30]:
        - generic [ref=e31]:
          - generic [ref=e32]: Nom de l'organisation
          - heading "Quel est le nom de votre boutique ?" [level=3] [ref=e33]
        - generic [ref=e34]:
          - 'textbox "ex: Bloom Industries" [active] [ref=e35]'
          - generic [ref=e36]:
            - img [ref=e37]
            - text: Au moins 3 caractères requis.
        - button "Continuer" [disabled] [ref=e40]:
          - text: Continuer
          - img [ref=e41]
    - generic:
      - generic: Stripe secure
      - generic: Michi 道 v2.5
  - alert [ref=e43]
```

# Test source

```ts
  1  | import { Page, expect } from '@playwright/test';
  2  | 
  3  | export class OnboardingPage {
  4  |   constructor(private page: Page) {}
  5  | 
  6  |   async completeStandaloneOnboarding(companyName: string) {
  7  |     // Stage 1: Org Name
  8  |     const nameInput = this.page.locator('[data-testid="org-name-input"]');
  9  |     await expect(nameInput).toBeVisible({ timeout: 15000 });
  10 |     
  11 |     // Ensure focus and fill (more reliable than pressSequentially for simple strings)
  12 |     await nameInput.click();
  13 |     await nameInput.fill(companyName);
  14 |     
  15 |     // Tiny delay to allow React state to settle
  16 |     await this.page.waitForTimeout(500);
  17 |     
  18 |     // Ensure the validation has passed and button is enabled
  19 |     const nextBtn = this.page.locator('[data-testid="onboarding-next"]');
  20 |     await expect(nextBtn).toBeEnabled({ timeout: 5000 });
  21 |     await nextBtn.click();
  22 |     
  23 |     // Stage 2: Plan Selection
  24 |     const finishBtn = this.page.locator('[data-testid="onboarding-finish"]');
  25 |     await expect(finishBtn).toBeVisible({ timeout: 10000 });
  26 |     await finishBtn.click();
  27 |     
  28 |     // WAIT for the navigation to Dashboard to settle
  29 |     console.log("Standalone onboarding finished. Waiting for dashboard navigation...");
  30 |     await expect(this.page).toHaveURL(/.*dashboard.*/, { timeout: 20000 });
  31 |     
  32 |     // Small buffer for React hydration on the new page
  33 |     await this.page.waitForLoadState('networkidle');
  34 |   }
  35 | 
  36 |   async completeDashboardWizard() {
  37 |     // Ensure we are stable on dashboard before looking for wizard
  38 |     await expect(this.page).toHaveURL(/.*dashboard.*/);
  39 |     
  40 |     // Wait to see if wizard overlay appears (it's a fixed portal)
  41 |     const startBtn = this.page.locator('[data-testid="wizard-start"]');
  42 |     
  43 |     // Check if the wizard overlay is visible (up to 8s wait for slow hydrations)
  44 |     const isWizardVisible = await startBtn.isVisible({ timeout: 8000 }).catch(() => false);
  45 |     
  46 |     if (isWizardVisible) {
  47 |       console.log("Onboarding wizard overlay detected. Completing...");
  48 |       await startBtn.click();
  49 |       await this.page.waitForTimeout(1000); // Animation buffer
  50 |       
  51 |       // Step 1: Connect
  52 |       const csvBtn = this.page.locator('[data-testid="wizard-platform-csv"]');
> 53 |       await expect(csvBtn).toBeVisible({ timeout: 15000 });
     |                            ^ Error: expect(locator).toBeVisible() failed
  54 |       await csvBtn.click();
  55 |       
  56 |       const nextBtn = this.page.locator('[data-testid="wizard-next"]');
  57 |       await expect(nextBtn).toBeEnabled({ timeout: 5000 });
  58 |       await nextBtn.click();
  59 |       await this.page.waitForTimeout(1000); // Animation buffer
  60 |       
  61 |       // Step 2: Analysis (Wait for sync simulation)
  62 |       const finishBtn = this.page.locator('[data-testid="wizard-finish"]');
  63 |       await expect(finishBtn).toBeVisible({ timeout: 25000 });
  64 |       await finishBtn.click();
  65 |       await this.page.waitForTimeout(1000);
  66 |       
  67 |       // Step 3: Ready
  68 |       const enterBtn = this.page.locator('[data-testid="wizard-enter"]');
  69 |       await expect(enterBtn).toBeVisible({ timeout: 15000 });
  70 |       await enterBtn.click();
  71 |       
  72 |       // Final wait for overlay to vanish
  73 |       await expect(startBtn).not.toBeVisible({ timeout: 10000 });
  74 |     } else {
  75 |       console.log("No onboarding wizard detected on dashboard.");
  76 |     }
  77 |   }
  78 | 
  79 |   async completeWizard(companyName: string = 'Test Organization') {
  80 |     // This helper orchestrates the whole flow
  81 |     const currentUrl = this.page.url();
  82 |     
  83 |     if (currentUrl.includes('/onboarding')) {
  84 |       await this.completeStandaloneOnboarding(companyName);
  85 |     }
  86 |     
  87 |     // Now we should be on /dashboard (or similar), try the wizard
  88 |     await this.completeDashboardWizard();
  89 |   }
  90 | }
  91 | 
```