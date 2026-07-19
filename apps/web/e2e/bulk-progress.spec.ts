import { expect, test } from "@playwright/test";

// Bulk generation: the live X-of-N progress bar + per-item status (GAP #2), against the mock backend.
test("runs a bulk batch to completion with per-item status", async ({ page }) => {
  await page.goto("/");

  // Wait for the table so the bulk button knows the current page's customer ids.
  await expect(page.locator("table tbody tr").first()).toBeVisible();

  const bulk = page.getByRole("button", { name: /Generate pitches for these/ });
  await expect(bulk).toBeEnabled();
  await bulk.click();

  // Progress reaches "N of N · done"; at least one item badge shows succeeded.
  await expect(page.getByText(/Bulk generation —/)).toBeVisible();
  await expect(page.getByText(/· done/)).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("succeeded").first()).toBeVisible();
});
