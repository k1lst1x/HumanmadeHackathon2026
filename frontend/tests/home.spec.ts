import { expect, test } from "@playwright/test";

test("shows the TextShop starter screen", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Agent-run company prototype" })).toBeVisible();
  await expect(page.getByText("Backend", { exact: true })).toBeVisible();
});
