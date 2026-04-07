import { test, expect } from "@playwright/test";

test.describe("Math Tool", () => {
  test("happy path: user asks math question and gets correct answer with tool card", async ({
    page,
  }) => {
    await page.goto("/");

    const input = page.locator("textarea");
    await input.fill("What is 125 * 8?");
    await input.press("Enter");

    const toolCard = page.locator("[data-tool-name='calculate']");
    await expect(toolCard).toBeVisible({ timeout: 30000 });

    await expect(toolCard).toContainText("Calculator");

    const assistantMessage = page.locator("text=1000");
    await expect(assistantMessage).toBeVisible({ timeout: 30000 });
  });

  test("error: division by zero shows error state in tool card", async ({
    page,
  }) => {
    await page.goto("/");

    const input = page.locator("textarea");
    await input.fill("What is 5 divided by 0?");
    await input.press("Enter");

    const toolCard = page.locator("[data-tool-name='calculate']");
    await expect(toolCard).toBeVisible({ timeout: 30000 });

    await expect(toolCard).toContainText("Error");
  });

  test("conversation reload: tool card reappears after page refresh", async ({
    page,
  }) => {
    await page.goto("/");

    const input = page.locator("textarea");
    await input.fill("Calculate sqrt(144)");
    await input.press("Enter");

    const toolCard = page.locator("[data-tool-name='calculate']");
    await expect(toolCard).toBeVisible({ timeout: 30000 });

    await expect(toolCard).toContainText("Calculator");

    const currentUrl = page.url();
    await page.reload();
    await page.waitForLoadState("networkidle");

    const reloadedToolCard = page.locator("[data-tool-name='calculate']");
    await expect(reloadedToolCard).toBeVisible({ timeout: 10000 });
    await expect(reloadedToolCard).toContainText("Calculator");
  });
});
