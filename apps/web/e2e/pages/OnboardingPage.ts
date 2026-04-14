import { Page, expect } from '@playwright/test';

export class OnboardingPage {
  constructor(private page: Page) {}

  async completeWizard() {
    // Step 0: Welcome
    await this.page.click('text=Démarrer la configuration');
    
    // Step 1: Connect (Select CSV for simplicity)
    await this.page.click('text=CSV/Excel');
    await this.page.click('button:has-text("Connecter")');
    
    // Step 2: Analysis (Wait for sync simulation)
    // The button text is "Finaliser l'analyse"
    await this.page.click('text=Finaliser l\'analyse', { timeout: 10000 });
    
    // Step 3: Ready
    await this.page.click('text=Entrer dans Michi');
  }

  async skipWizard() {
    await this.page.click('text=Passer la configuration (Expert)');
  }

  async expectSuccess() {
    await expect(this.page.locator('text=Tableau de bord')).toBeVisible();
    await expect(this.page).toHaveURL(/.*dashboard/);
  }
}
