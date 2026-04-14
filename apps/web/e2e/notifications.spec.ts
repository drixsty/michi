import { test, expect } from '@playwright/test';
import { AuthPage } from './pages/AuthPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { DashboardPage } from './pages/DashboardPage';

test.describe('Notifications & Real-time Alerts', () => {
  let authPage: AuthPage;
  let onboardingPage: OnboardingPage;
  let dashboardPage: DashboardPage;
  
  const testUser = {
    email: `notif-${Math.floor(Math.random() * 10000)}@michi.com`,
    password: 'Password123!',
    firstName: 'Notif',
    lastName: 'Tester'
  };

  test('Receive and Manage Inventory Alerts', async ({ page }) => {
    authPage = new AuthPage(page);
    onboardingPage = new OnboardingPage(page);
    dashboardPage = new DashboardPage(page);

    // 1. Setup
    await authPage.gotoRegister();
    await authPage.register(testUser.firstName, testUser.lastName, testUser.email, testUser.password);
    await onboardingPage.completeWizard();
    
    // 2. Trigger Alerts (Sync generates data, some will be low stock)
    await dashboardPage.switchTab('inventory');
    await dashboardPage.triggerSync();

    // 3. Check Notification Bell
    const bellBadge = page.locator('[data-testid="notification-badge"]');
    // Wait for alerts to be generated and processed (poll)
    await expect(bellBadge).toBeVisible({ timeout: 10000 });
    const count = await bellBadge.innerText();
    expect(parseInt(count)).toBeGreaterThan(0);

    // 4. Open and Read
    await dashboardPage.openNotifications();
    await expect(page.locator('text=Alertes Stockout')).toBeVisible();
    
    await dashboardPage.markAllNotificationsAsRead();
    await expect(bellBadge).not.toBeVisible();
  });
});
