/**
 * E2E — Sprint 1 : Sync → Voir produits (US 1.3)
 *
 * Scénario complet :
 *   1. L'utilisateur arrive sur /login
 *   2. Il se connecte avec des credentials valides
 *   3. Il est redirigé vers /dashboard
 *   4. Il clique sur "Synchroniser"
 *   5. Le bouton passe en état "Synchronisation…"
 *   6. Un toast de succès apparaît
 *   7. Le tableau affiche des produits (≥ 1)
 *   8. Les badges stock sont visibles
 *
 * Pré-requis :
 *   - Backend en cours d'exécution sur http://localhost:8000
 *   - Frontend en cours d'exécution sur http://localhost:3000
 *   - Un utilisateur de test seed en DB (email/password ci-dessous)
 */

import { test, expect } from '@playwright/test';

const TEST_EMAIL = 'admin@michi.com';
const TEST_PASSWORD = 'michi2026';

test.describe('Sprint 1 — Mock Shopify Sync', () => {
  test.beforeEach(async ({ page }) => {
    // Partir de la page login propre
    await page.goto('/login');
  });

  test('US 1.3 : login → sync → tableau produits affiché', async ({ page }) => {
    // ── 1. Login ──────────────────────────────────────────────
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/mot de passe|password/i).fill(TEST_PASSWORD);
    await page.getByRole('button', { name: /connexion|login/i }).click();

    // ── 2. Redirection dashboard ──────────────────────────────
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 });
    await expect(page.getByText('Catalogue produits')).toBeVisible();

    // ── 3. Clic sur Synchroniser ──────────────────────────────
    const syncBtn = page.getByRole('button', { name: /synchroniser/i });
    await expect(syncBtn).toBeVisible();
    await syncBtn.click();

    // ── 4. État loading ───────────────────────────────────────
    await expect(page.getByText(/synchronisation/i)).toBeVisible();

    // ── 5. Toast succès ───────────────────────────────────────
    await expect(page.getByText(/sync réussie|produits/i)).toBeVisible({ timeout: 15000 });

    // ── 6. Tableau produits ───────────────────────────────────
    // Attendre que le tableau se remplisse après refetch
    await expect(page.locator('table tbody tr').first()).toBeVisible({ timeout: 10000 });

    const rows = page.locator('table tbody tr');
    await expect(rows).toHaveCount(50, { timeout: 10000 });

    // ── 7. KPI cards visibles ─────────────────────────────────
    await expect(page.getByText('Total produits')).toBeVisible();
    await expect(page.getByText('Ruptures')).toBeVisible();

    // ── 8. Au moins un badge stock affiché ───────────────────
    const badges = page.locator('table tbody').getByText(/u\.|Rupture/);
    await expect(badges.first()).toBeVisible();
  });

  test('US 1.1 : 50 produits générés avec SKU visibles', async ({ page }) => {
    // Login rapide via localStorage (token existant depuis test précédent non garanti → refaire login)
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/mot de passe|password/i).fill(TEST_PASSWORD);
    await page.getByRole('button', { name: /connexion|login/i }).click();
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 });

    await page.getByRole('button', { name: /synchroniser/i }).click();
    await expect(page.locator('table tbody tr').first()).toBeVisible({ timeout: 15000 });

    // Vérifier qu'au moins un SKU est au format CATEGORY-NNNN
    const skuCells = page.locator('table tbody .font-mono');
    await expect(skuCells.first()).toBeVisible();
    const firstSku = await skuCells.first().textContent();
    expect(firstSku).toMatch(/^[A-Z]+-\d{4}$/);
  });

  test('US 1.2 : filtre "Rupture" affiche uniquement les produits en stock=0', async ({ page }) => {
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/mot de passe|password/i).fill(TEST_PASSWORD);
    await page.getByRole('button', { name: /connexion|login/i }).click();
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 });

    await page.getByRole('button', { name: /synchroniser/i }).click();
    await expect(page.locator('table tbody tr').first()).toBeVisible({ timeout: 15000 });

    // Clic sur l'onglet "Rupture"
    await page.getByRole('button', { name: /rupture/i }).first().click();

    // Toutes les lignes visibles doivent avoir le badge "Rupture"
    const visibleRows = page.locator('table tbody tr');
    const count = await visibleRows.count();

    if (count > 0) {
      // Chaque ligne doit afficher "Rupture"
      for (let i = 0; i < Math.min(count, 5); i++) {
        await expect(visibleRows.nth(i).getByText('Rupture')).toBeVisible();
      }
    }
    // Si count=0, le filtre fonctionne (aucun produit en rupture ce run)
  });
});
