import { expect, test } from "@playwright/test";

test("shows the TextShop landing page", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "textshop" })).toBeVisible();
  await expect(page.getByText("pitch decks by text", { exact: false })).toBeVisible();
});
