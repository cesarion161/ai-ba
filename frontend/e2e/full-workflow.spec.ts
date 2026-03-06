import { test, expect } from "@playwright/test";

test.describe("Full Workflow", () => {
  test("should show welcome screen on initial load", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("AI Business Analysis")).toBeVisible();
    await expect(page.getByText("Projects")).toBeVisible();
  });

  test("should create a new project from chat", async ({ page }) => {
    await page.goto("/");

    // Click new project button
    await page.getByText("+ New Project").click();

    // Fill in the prompt
    await page.getByPlaceholder(/describe your business/i).fill(
      "A subscription box service for artisan coffee"
    );
    await page.getByText("Start Analysis").click();

    // Should show the project in the list
    await expect(page.getByText(/artisan coffee/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("should display project list", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Projects")).toBeVisible();
  });
});
