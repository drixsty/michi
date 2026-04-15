import { Page, expect } from '@playwright/test';

export class OnboardingPage {
  constructor(private page: Page) {}

  async completeStandaloneOnboarding(companyName: string) {
    // Stage 1: Org Name
    const nameInput = this.page.locator('[data-testid="org-name-input"]');
    await expect(nameInput).toBeVisible({ timeout: 15000 });
    
    // Human-like typing to ensure React state captures the input
    await nameInput.focus();
    await nameInput.clear();
    await nameInput.pressSequentially(companyName, { delay: 100 });
    
    const nextBtn = this.page.locator('[data-testid="onboarding-next"]');
    await expect(nextBtn).toBeEnabled({ timeout: 5000 });
    await nextBtn.click();
    
    // Stage 2: Plan Selection
    const finishBtn = this.page.locator('[data-testid="onboarding-finish"]');
    await expect(finishBtn).toBeVisible({ timeout: 10000 });
    await finishBtn.click();
    
    // WAIT for the navigation to Dashboard to settle
    console.log("Standalone onboarding finished. Waiting for dashboard navigation...");
    await this.page.waitForURL(/.*dashboard.*/, { timeout: 20000 });
    
    // Small buffer for React hydration on the new page
    await this.page.waitForLoadState('networkidle');
  }

  async completeDashboardWizard() {
    // Wait to see if wizard overlay appears
    const startBtn = this.page.locator('[data-testid="wizard-start"]');
    
    // Check if the wizard overlay is visible (up to 5s wait)
    const isWizardVisible = await startBtn.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (isWizardVisible) {
      console.log("Onboarding wizard overlay detected. Completing...");
      await startBtn.click();
      await this.page.waitForTimeout(1000); // Animation buffer
      
      // Step 1: Connect
      const csvBtn = this.page.locator('[data-testid="wizard-platform-csv"]');
      await expect(csvBtn).toBeVisible({ timeout: 10000 });
      await csvBtn.click();
      
      const nextBtn = this.page.locator('[data-testid="wizard-next"]');
      await expect(nextBtn).toBeEnabled();
      await nextBtn.click();
      await this.page.waitForTimeout(1000); // Animation buffer
      
      // Step 2: Analysis (Wait for sync simulation)
      const finishBtn = this.page.locator('[data-testid="wizard-finish"]');
      await expect(finishBtn).toBeVisible({ timeout: 20000 });
      await finishBtn.click();
      await this.page.waitForTimeout(1000);
      
      // Step 3: Ready
      const enterBtn = this.page.locator('[data-testid="wizard-enter"]');
      await expect(enterBtn).toBeVisible({ timeout: 10000 });
      await enterBtn.click();
    } else {
      console.log("No onboarding wizard detected on dashboard.");
    }
  }

  async completeWizard(companyName: string = 'Test Organization') {
    // This helper orchestrates the whole flow
    const currentUrl = this.page.url();
    
    if (currentUrl.includes('/onboarding')) {
      await this.completeStandaloneOnboarding(companyName);
    }
    
    // Now we should be on /dashboard (or similar), try the wizard
    await this.completeDashboardWizard();
  }
}
