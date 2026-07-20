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
