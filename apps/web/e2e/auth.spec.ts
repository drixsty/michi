import { test, expect, Page } from '@playwright/test';
import { AuthPage } from './pages/AuthPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { DashboardPage } from './pages/DashboardPage';

// We use mode: 'serial' to ensure tests run in order and share the account creation state
test.describe.configure({ mode: 'serial' });

test.describe('Authentication & Onboarding Flow', () => {
  // We use a shared page to maintain the session across serial tests
  let sharedPage: Page;
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
    sharedPage = await browser.newPage();
    authPage = new AuthPage(sharedPage);
    onboardingPage = new OnboardingPage(sharedPage);
    dashboardPage = new DashboardPage(sharedPage);
  });

  test.afterAll(async () => {
    await sharedPage.close();
  });

  test('1. Full Registration and Onboarding Flow', async () => {
    await authPage.gotoRegister();
    await authPage.register(testUser.firstName, testUser.lastName, testUser.email, testUser.password);
    
    // Check we landed on onboarding or dashboard
    await expect(sharedPage).toHaveURL(/.*(dashboard|onboarding)/, { timeout: 15000 });
    
    // Complete the Onboarding Wizard (both standalone and dashboard parts)
    await onboardingPage.completeWizard();
    
    await dashboardPage.expectLoggedIn();
  });

  test('2. Logout Flow', async () => {
    // Session is maintained from test #1
    await dashboardPage.goto();
    await dashboardPage.expectLoggedIn();
    
    await dashboardPage.logout();
    await expect(sharedPage).toHaveURL(/.*login/);
  });

  test('3. Successful Login with created user', async () => {
    await authPage.gotoLogin();
    await authPage.login(testUser.email, testUser.password);
    await dashboardPage.expectLoggedIn();
  });

  test('4. Login Failure with wrong password', async () => {
    await authPage.gotoLogin();
    await authPage.login(testUser.email, 'wrongpassword');
    await authPage.expectError('Identifiants incorrects');
  });

  test('5. Registration Failure - Email already exists', async () => {
    await authPage.gotoRegister();
    // Use testUser.email which was registered in test #1
    await authPage.register('Duplicate', 'User', testUser.email, testUser.password);
    await authPage.expectError('déjà utilisé');
  });

  test('6. Organization Switching', async () => {
    await authPage.gotoLogin();
    await authPage.login(testUser.email, testUser.password);
    await dashboardPage.expectLoggedIn();
    
    await dashboardPage.openOrgSwitcher();
    // Verify the switcher works
    await expect(sharedPage.locator('text=Changer d\'organisation')).toBeVisible();
    await sharedPage.click('text=Fermer'); 
  });
});
