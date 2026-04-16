import { Page, expect } from '@playwright/test';

export class OnboardingPage {
  constructor(private page: Page) {}

  async completeStandaloneOnboarding(companyName: string) {
    // Stage 1: Org Name
    const nameInput = this.page.locator('[data-testid="org-name-input"]');
    await expect(nameInput).toBeVisible({ timeout: 15000 });
    
    // Ensure focus and fill (more reliable than pressSequentially for simple strings)
    await nameInput.click();
    await nameInput.fill(companyName);
    
    // Tiny delay to allow React state to settle
    await this.page.waitForTimeout(500);
    
    // Ensure the validation has passed and button is enabled
    const nextBtn = this.page.locator('[data-testid="onboarding-next"]');
    await expect(nextBtn).toBeEnabled({ timeout: 5000 });
    await nextBtn.click();
    
    // Stage 2: Plan Selection
    const finishBtn = this.page.locator('[data-testid="onboarding-finish"]');
    await expect(finishBtn).toBeVisible({ timeout: 10000 });
    await finishBtn.click();
    
    // WAIT for the navigation to Dashboard to settle
    console.log("Standalone onboarding finished. Waiting for dashboard navigation...");
    await expect(this.page).toHaveURL(/.*dashboard.*/, { timeout: 20000 });
    
    // Small buffer for React hydration on the new page
    await this.page.waitForLoadState('networkidle');
  }

  async completeDashboardWizard() {
    // Ensure we are stable on dashboard before looking for wizard
    await expect(this.page).toHaveURL(/.*dashboard.*/);
    
    // Wait to see if wizard overlay appears (it's a fixed portal)
    const startBtn = this.page.locator('[data-testid="wizard-start"]');
    
    // Check if the wizard overlay is visible (up to 8s wait for slow hydrations)
    const isWizardVisible = await startBtn.isVisible({ timeout: 8000 }).catch(() => false);
    
    if (isWizardVisible) {
      console.log("Onboarding wizard overlay detected. Completing...");
      await startBtn.click();
      await this.page.waitForTimeout(1000); // Animation buffer
      
      // Step 1: Connect
      const csvBtn = this.page.locator('[data-testid="wizard-platform-csv"]');
      await expect(csvBtn).toBeVisible({ timeout: 15000 });
      await csvBtn.click();
      
      const nextBtn = this.page.locator('[data-testid="wizard-next"]');
      await expect(nextBtn).toBeEnabled({ timeout: 5000 });
      await nextBtn.click();
      await this.page.waitForTimeout(1000); // Animation buffer
      
      // Step 2: Analysis (Wait for sync simulation)
      const finishBtn = this.page.locator('[data-testid="wizard-finish"]');
      await expect(finishBtn).toBeVisible({ timeout: 25000 });
      await finishBtn.click();
      await this.page.waitForTimeout(1000);
      
      // Step 3: Ready
      const enterBtn = this.page.locator('[data-testid="wizard-enter"]');
      await expect(enterBtn).toBeVisible({ timeout: 15000 });
      await enterBtn.click();
      
      // Final wait for overlay to vanish
      await expect(startBtn).not.toBeVisible({ timeout: 10000 });
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
