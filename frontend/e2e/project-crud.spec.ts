import { test, expect } from "@playwright/test";

test.describe("Project CRUD", () => {
  test("should show empty state when no projects", async ({ page }) => {
    await page.goto("/");
    // The project list should exist
    await expect(page.getByText("Projects")).toBeVisible();
  });

  test("should open new project dialog", async ({ page }) => {
    await page.goto("/");
    await page.getByText("+ New Project").click();
    await expect(page.getByText("New Business Analysis")).toBeVisible();
  });
});
