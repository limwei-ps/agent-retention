import { expect, test } from "@playwright/test";

// Bulk generation: the live X-of-N progress bar + per-item status (GAP #2), against the mock backend.
test("runs a bulk batch to completion with per-item status", async ({ page }) => {
  await page.goto("/");

  // Wait for the table so the bulk button knows the current page's customer ids.
  await expect(page.locator("table tbody tr").first()).toBeVisible();

  const bulk = page.getByRole("button", { name: /Generate pitches for these/ });
  await expect(bulk).toBeEnabled();
  await bulk.click();

  // The bulk panel appears, reaches "Done", and shows at least one Ready item.
  const panel = page.getByRole("region", { name: /bulk generation progress/i });
  await expect(panel).toBeVisible();
  await expect(panel.getByText("Done")).toBeVisible({ timeout: 30_000 });
  await expect(panel.getByText("Ready").first()).toBeVisible();
});

// The bulk panel lives in a layout-level provider, so it must survive navigating into a pitch and back,
// and reset when the list filter changes.
test("bulk panel survives navigation and resets on filter change", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("table tbody tr").first()).toBeVisible();
  await page.getByRole("button", { name: /Generate pitches for these/ }).click();

  const panel = page.getByRole("region", { name: /bulk generation progress/i });
  await expect(panel.getByText("Done")).toBeVisible({ timeout: 30_000 });

  // Open a generated pitch, then go back — the panel must still be there (bug #1).
  await panel
    .getByRole("link", { name: /open pitch/i })
    .first()
    .click();
  await expect(page).toHaveURL(/\/customers\//);
  await page.goBack();
  await expect(panel).toBeVisible();
  await expect(panel.getByText("Done")).toBeVisible();

  // Change the filter via a dashboard-summary tile — the stale panel must clear (bug #2).
  await page.getByRole("button", { name: /All plans/i }).click();
  await expect(panel).toHaveCount(0);
});
