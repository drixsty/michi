# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Authentication & Onboarding Flow >> 2. Logout Flow
- Location: e2e\auth.spec.ts:47:7

# Error details

```
Test timeout of 60000ms exceeded.
```

```
Error: locator.click: Target page, context or browser has been closed
Call log:
  - waiting for locator('[data-testid="user-menu-button"][data-user-loaded="true"]')
    - locator resolved to <button data-user-loaded="true" data-testid="user-menu-button" class="w-9 h-9 rounded-full bg-accent border border-border flex items-center justify-center overflow-hidden ml-1 hover:bg-accent/80 transition-colors">…</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-md p-4">…</div> from <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">…</main> subtree intercepts pointer events
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-md p-4">…</div> from <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">…</main> subtree intercepts pointer events
    - retrying click action
      - waiting 100ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-md p-4">…</div> from <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">…</main> subtree intercepts pointer events
    - retrying click action
      - waiting 500ms
  - element was detached from the DOM, retrying
    - waiting for" http://localhost:3000/onboarding" navigation to finish...
    - navigated to "http://localhost:3000/onboarding"

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
            - heading "Initialisez votre espace." [level=2] [ref=e13]:
              - text: Initialisez
              - text: votre espace.
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
          - heading "Quel est le nom de votre boutique ?" [level=3] [ref=e33]:
            - text: Quel est le nom
            - text: de votre boutique ?
        - generic [ref=e34]:
          - 'textbox "ex: Bloom Industries" [active] [ref=e35]'
          - generic [ref=e36]:
            - img [ref=e37]
            - text: À moins de 3 caractères requis.
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
  3  | export class DashboardPage {
  4  |   constructor(private page: Page) {}
  5  | 
  6  |   async goto() {
  7  |     await this.page.goto('/fr/dashboard');
  8  |   }
  9  | 
  10 |   async logout() {
  11 |     // Wait for the user data to be loaded and UI to stabilize
  12 |     const menuBtn = this.page.locator('[data-testid="user-menu-button"][data-user-loaded="true"]');
  13 |     await menuBtn.waitFor({ state: 'visible', timeout: 15000 });
  14 |     
  15 |     // Click the button to toggle the menu
> 16 |     await menuBtn.click();
     |                   ^ Error: locator.click: Target page, context or browser has been closed
  17 |     
  18 |     // Click the logout button
  19 |     const logoutBtn = this.page.locator('[data-testid="logout-button"]');
  20 |     await logoutBtn.waitFor({ state: 'visible' });
  21 |     await logoutBtn.click();
  22 |   }
  23 | 
  24 |   async switchTab(name: 'overview' | 'inventory' | 'sources' | 'decisions' | 'organization') {
  25 |     await this.page.click(`[data-testid="nav-${name}"]`);
  26 |     // Wait for the tab to be active in URL or content
  27 |     await expect(this.page).toHaveURL(new RegExp(`tab=${name}|dashboard$`));
  28 |   }
  29 | 
  30 |   async searchProduct(query: string) {
  31 |     await this.page.fill('[data-testid="search-input"]', query);
  32 |     await this.page.press('[data-testid="search-input"]', 'Enter');
  33 |   }
  34 | 
  35 |   async triggerSync() {
  36 |     await this.page.click('[data-testid="sync-button"]');
  37 |     // Wait for the sync toast/message
  38 |     await expect(this.page.locator('text=Synchronisation réussie')).toBeVisible({ timeout: 15000 });
  39 |   }
  40 | 
  41 |   async openNotifications() {
  42 |     await this.page.click('[data-testid="notification-bell"]');
  43 |     await expect(this.page.locator('[data-testid="notification-panel"]')).toBeVisible();
  44 |   }
  45 | 
  46 |   async markAllNotificationsAsRead() {
  47 |     await this.page.click('[data-testid="mark-all-read"]');
  48 |   }
  49 | 
  50 |   async openOrgSwitcher() {
  51 |     await this.page.click('[data-testid="user-menu-button"]');
  52 |     await this.page.click('[data-testid="org-switcher-button"]');
  53 |   }
  54 | 
  55 |   async selectOrganization(name: string) {
  56 |     await this.page.click(`text=${name}`);
  57 |     // Wait for the switch to complete (indicated by menu close or toast)
  58 |     await expect(this.page.locator('[data-testid="org-switcher-button"]')).not.toBeVisible();
  59 |   }
  60 | 
  61 |   async navigateToProductDetail(id: string) {
  62 |     await this.page.goto(`/fr/dashboard/product/${id}`);
  63 |     await expect(this.page.locator('[data-testid="product-detail-view"]')).toBeVisible();
  64 |   }
  65 | 
  66 |   async openProductDetail(sku: string) {
  67 |     await this.page.click(`text=${sku}`);
  68 |     await expect(this.page.locator('[data-testid="product-quickview"]')).toBeVisible();
  69 |   }
  70 | 
  71 |   async expectLoggedIn() {
  72 |     await expect(this.page).toHaveURL(/.*dashboard/);
  73 |   }
  74 | }
  75 | 
```