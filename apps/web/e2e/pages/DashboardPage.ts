import { Page, expect } from '@playwright/test';

export class DashboardPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/fr/dashboard');
  }

  async logout() {
    // Wait for the user data to be loaded and UI to stabilize
    const menuBtn = this.page.locator('[data-testid="user-menu-button"][data-user-loaded="true"]');
    await menuBtn.waitFor({ state: 'visible', timeout: 15000 });
    
    // Click the button to toggle the menu
    await menuBtn.click();
    
    // Click the logout button
    const logoutBtn = this.page.locator('[data-testid="logout-button"]');
    await logoutBtn.waitFor({ state: 'visible' });
    await logoutBtn.click();
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

  async openNotifications() {
    await this.page.click('[data-testid="notification-bell"]');
    await expect(this.page.locator('[data-testid="notification-panel"]')).toBeVisible();
  }

  async markAllNotificationsAsRead() {
    await this.page.click('[data-testid="mark-all-read"]');
  }

  async openOrgSwitcher() {
    await this.page.click('[data-testid="user-menu-button"]');
    await this.page.click('[data-testid="org-switcher-button"]');
  }

  async selectOrganization(name: string) {
    await this.page.click(`text=${name}`);
    // Wait for the switch to complete (indicated by menu close or toast)
    await expect(this.page.locator('[data-testid="org-switcher-button"]')).not.toBeVisible();
  }

  async navigateToProductDetail(id: string) {
    await this.page.goto(`/fr/dashboard/product/${id}`);
    await expect(this.page.locator('[data-testid="product-detail-view"]')).toBeVisible();
  }

  async openProductDetail(sku: string) {
    await this.page.click(`text=${sku}`);
    await expect(this.page.locator('[data-testid="product-quickview"]')).toBeVisible();
  }

  async expectLoggedIn() {
    await expect(this.page).toHaveURL(/.*dashboard/);
  }
}
