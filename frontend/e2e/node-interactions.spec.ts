import { test, expect } from "@playwright/test";

test.describe("Node Interactions", () => {
  test("should show welcome screen initially", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByText("AI Business Analysis").first()
    ).toBeVisible();
  });
});
