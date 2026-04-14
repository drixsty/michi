import { Page, expect } from '@playwright/test';

export class AuthPage {
  constructor(private page: Page) {}

  async gotoLogin() {
    await this.page.goto('/login');
  }

  async gotoRegister() {
    await this.page.goto('/register');
  }

  async login(email: string, password: string) {
    await this.page.fill('input[type="email"]', email);
    await this.page.fill('input[type="password"]', password);
    await this.page.click('button[type="submit"]');
  }

  async register(firstName: string, lastName: string, email: string, password: string) {
    await this.page.getByPlaceholder('Jean').fill(firstName);
    await this.page.getByPlaceholder('Dupont').fill(lastName);
    await this.page.fill('input[type="email"]', email);
    await this.page.fill('input[type="password"]', password);
    await this.page.click('button[type="submit"]');
  }

  async expectError(message: string) {
    const error = this.page.locator('div.text-red-600');
    await expect(error).toBeVisible();
    await expect(error).toContainText(message);
  }
}
