import { expect, test } from "@playwright/test";

// Streaming pitch: the graded core. Drives the real UI against the mock backend and asserts the state
// machine transitions (generating → ready) and the grounded output — the "watch it stream" teeth step,
// automated. Robust to whether the customer already has a pitch (tests share one seeded backend).
test("streams a grounded pitch and supports copy + regenerate", async ({ page }) => {
  await page.goto("/");

  const firstCustomer = page.locator("table tbody tr td a").first();
  await expect(firstCustomer).toBeVisible();
  await firstCustomer.click();
  await expect(page).toHaveURL(/\/customers\/CUST-/);

  // The primary action is "Generate" (no pitch) or "Regenerate" (already ready) — click either.
  const action = page.getByRole("button", { name: /^(Generate|Regenerate)$/ });
  await expect(action).toBeVisible();
  await action.click();

  // Streaming proof: the status badge passes through "Generating" before settling on "Ready".
  await expect(page.getByText("Generating", { exact: true })).toBeVisible();
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();

  // Grounded output: the mock always references TIME and an RM price from the real offer.
  const pitch = page.locator("main p.whitespace-pre-wrap");
  await expect(pitch).toContainText("TIME");
  await expect(pitch).toContainText("RM");

  // Copy flips the button label.
  await page.getByRole("button", { name: "Copy" }).click();
  await expect(page.getByRole("button", { name: "Copied!" })).toBeVisible();

  // Regenerate (force) runs another generation and lands back on Ready with grounded text.
  await page.getByRole("button", { name: "Regenerate" }).click();
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  await expect(pitch).toContainText("TIME");
});
