import { Page, expect } from '@playwright/test';

export class SettingsPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/fr/dashboard/settings');
    await expect(this.page.locator('text=Paramètres')).toBeVisible();
  }

  async inviteMember(email: string, role: 'ADMIN' | 'VIEWER' | 'MANAGER' = 'VIEWER') {
    await this.page.click('[data-testid="add-member-button"]');
    await this.page.fill('[data-testid="invite-email-input"]', email);
    // Select role if provided (assuming a select or radio buttons)
    // await this.page.selectOption('[data-testid="role-select"]', role);
    await this.page.click('[data-testid="send-invite-button"]');
    await expect(this.page.locator(`text=${email}`)).toBeVisible();
  }

  async upgradeToPro() {
    await this.page.click('[data-testid="upgrade-pro-button"]');
    // Assuming a MOCK checkout or local state change
    await expect(this.page.locator('text=Plan Pro Actif')).toBeVisible();
  }
}
