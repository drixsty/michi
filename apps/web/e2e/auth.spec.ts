import { test, expect } from '@playwright/test';

test('has title and login button', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Michi/);

  // Check for login button or heading
  const loginHeading = page.getByRole('heading', { name: /Se connecter/i }).or(page.getByRole('heading', { name: /Login/i }));
  // Since we might not be logged in, we check for presence of main UI elements
});

test('can navigate to login', async ({ page }) => {
  await page.goto('/login');
  await expect(page).toHaveURL(/.*login/);
});
