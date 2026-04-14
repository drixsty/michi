import { Page, expect } from '@playwright/test';

export class DashboardPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/dashboard');
  }

  async logout() {
    // Hover the user menu to reveal the logout button
    await this.page.hover('[data-testid="user-menu-button"]');
    await this.page.click('[data-testid="logout-button"]');
  }

  async switchTab(name: 'overview' | 'inventory' | 'sources' | 'decisions' | 'organization') {
    await this.page.click(`[data-testid="nav-${name}"]`);
    // Wait for the tab to be active in URL or content
    await expect(this.page).toHaveURL(new RegExp(`tab=${name}|dashboard$`));
  }

  async searchProduct(query: string) {
    await this.page.fill('[data-testid="search-input"]', query);
    await this.page.press('[data-testid="search-input"]', 'Enter');
  }

  async triggerSync() {
    await this.page.click('[data-testid="sync-button"]');
    // Wait for the sync toast/message
    await expect(this.page.locator('text=Synchronisation réussie')).toBeVisible({ timeout: 15000 });
  }

  async openProductDetail(sku: string) {
    await this.page.click(`text=${sku}`);
    await expect(this.page.locator('[data-testid="product-quickview"]')).toBeVisible();
  }

  async expectLoggedIn() {
    await expect(this.page).toHaveURL(/.*dashboard/);
  }
}
