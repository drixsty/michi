import { test, expect } from '@playwright/test';
import { AuthPage } from './pages/AuthPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { DashboardPage } from './pages/DashboardPage';
import { SettingsPage } from './pages/SettingsPage';

test.describe('Settings, Team & Billing', () => {
  let authPage: AuthPage;
  let onboardingPage: OnboardingPage;
  let dashboardPage: DashboardPage;
  let settingsPage: SettingsPage;
  
  const testUser = {
    email: `settings-${Math.floor(Math.random() * 10000)}@michi.com`,
    password: 'Password123!',
    firstName: 'Settings',
    lastName: 'Tester'
  };

  test('Manage Team and Upgrade Plan', async ({ page }) => {
    authPage = new AuthPage(page);
    onboardingPage = new OnboardingPage(page);
    dashboardPage = new DashboardPage(page);
    settingsPage = new SettingsPage(page);

    // 1. Setup
    await authPage.gotoRegister();
    await authPage.register(testUser.firstName, testUser.lastName, testUser.email, testUser.password);
    await onboardingPage.completeWizard();

    // 2. Settings - Invitations
    await dashboardPage.switchTab('organization');
    await settingsPage.inviteMember('colleague@michi.com', 'VIEWER');
    
    // 3. Settings - Billing (MOCK)
    // We assume there is a "Plan" section in implementation
    await settingsPage.upgradeToPro();
  });
});
