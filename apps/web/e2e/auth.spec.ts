import { test, expect } from '@playwright/test';
import { AuthPage } from './pages/AuthPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { DashboardPage } from './pages/DashboardPage';

test.describe.serial('Authentication & Onboarding Flow', () => {
  let authPage: AuthPage;
  let onboardingPage: OnboardingPage;
  let dashboardPage: DashboardPage;
  
  const testUser = {
    email: `test-${Math.floor(Math.random() * 10000)}@michi.com`,
    password: 'Password123!',
    firstName: 'E2E',
    lastName: 'Tester'
  };

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    authPage = new AuthPage(page);
    onboardingPage = new OnboardingPage(page);
    dashboardPage = new DashboardPage(page);
  });

  test('1. Full Registration and Onboarding Flow', async ({ page }) => {
    authPage = new AuthPage(page);
    onboardingPage = new OnboardingPage(page);
    dashboardPage = new DashboardPage(page);

    await authPage.gotoRegister();
    await authPage.register(testUser.firstName, testUser.lastName, testUser.email, testUser.password);
    
    await expect(page).toHaveURL(/.*dashboard(\?onboarding=true)?/);
    
    // Complete the Onboarding Wizard
    await onboardingPage.completeWizard();
    
    await dashboardPage.expectLoggedIn();
  });

  test('2. Logout Flow', async ({ page }) => {
    // Reuse session from previous test if possible, or login again
    authPage = new AuthPage(page);
    dashboardPage = new DashboardPage(page);
    
    await dashboardPage.goto();
    await dashboardPage.expectLoggedIn();
    
    await dashboardPage.logout();
    await expect(page).toHaveURL(/.*login/);
  });

  test('3. Successful Login with created user', async ({ page }) => {
    authPage = new AuthPage(page);
    dashboardPage = new DashboardPage(page);

    await authPage.gotoLogin();
    await authPage.login(testUser.email, testUser.password);
    await dashboardPage.expectLoggedIn();
  });

  test('4. Login Failure with wrong password', async ({ page }) => {
    authPage = new AuthPage(page);
    await authPage.gotoLogin();
    await authPage.login(testUser.email, 'wrongpassword');
    await authPage.expectError('Identifiants incorrects');
  });

  test.skip('5. Organization Switching', async ({ page }) => {
    authPage = new AuthPage(page);
    dashboardPage = new DashboardPage(page);

    await authPage.gotoLogin();
    await authPage.login(testUser.email, testUser.password);
    await dashboardPage.expectLoggedIn();
    
    await dashboardPage.openOrgSwitcher();
    await expect(page.locator('text=Changer d\'organisation')).toBeVisible();
  });
});
