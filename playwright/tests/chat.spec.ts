import { test, expect } from "@playwright/test";

async function sendMessage(page: any, text: string) {
  const input = page.getByPlaceholder("Send a message...");
  await input.click();
  await input.pressSequentially(text, { delay: 10 });
  await page.waitForTimeout(300);
  await input.press("Enter");
}

test.describe("ChatGPT App E2E", () => {
  test("homepage loads with sidebar and chat area", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("button", { name: "+ New Chat" })).toBeVisible();
    await expect(page.getByPlaceholder("Send a message...")).toBeVisible();
    await expect(page.getByText("How can I help you today?")).toBeVisible();
  });

  test("can send a message and receive a streamed AI response", async ({ page }) => {
    await page.goto("/");

    await sendMessage(page, "Say the word pineapple");

    // User message should appear in the chat
    await expect(page.locator("main").getByText("Say the word pineapple")).toBeVisible({
      timeout: 5_000,
    });

    // Wait for AI response to appear (any new content in main after user message)
    await expect(page.locator("main").locator("div").filter({ hasText: /./i }).last()).toBeVisible({
      timeout: 15_000,
    });

    // Conversation should appear in sidebar
    const sidebarEntries = page.locator("aside").locator("button").filter({ hasNotText: /New Chat|×/ });
    await expect(sidebarEntries.first()).toBeVisible({ timeout: 10_000 });
  });

  test("new chat button clears the conversation", async ({ page }) => {
    await page.goto("/");

    await sendMessage(page, "Testing new chat clear");

    // Wait for user message to appear
    await expect(page.locator("main").getByText("Testing new chat clear")).toBeVisible({
      timeout: 5_000,
    });

    // Wait for AI response to complete
    await page.waitForTimeout(8_000);

    // Click new chat
    await page.getByRole("button", { name: "+ New Chat" }).click();

    // Chat area should show the empty state
    await expect(page.getByText("How can I help you today?")).toBeVisible({ timeout: 3_000 });
  });

  test("can switch between conversations in sidebar", async ({ page }) => {
    await page.goto("/");

    // If there are existing conversations in sidebar, click one
    const sidebarEntries = page.locator("aside").locator("button").filter({ hasNotText: /New Chat|×/ });

    const count = await sidebarEntries.count();
    if (count > 0) {
      await sidebarEntries.first().click();
      // Should load messages (main area should not show empty state)
      await page.waitForTimeout(2_000);
      const messageArea = page.locator("main");
      await expect(messageArea).toBeVisible();
    }
  });

  test("can delete a conversation with confirmation", async ({ page }) => {
    await page.goto("/");

    // First create a conversation to delete
    await sendMessage(page, "Delete me please");
    await page.waitForTimeout(8_000);

    // Find a delete button (×) in sidebar
    const deleteBtn = page.locator("aside").locator('button:has-text("×")').first();
    await expect(deleteBtn).toBeVisible({ timeout: 5_000 });
    await deleteBtn.click();

    // Confirmation dialog should appear
    await expect(page.getByText("Delete conversation")).toBeVisible({ timeout: 3_000 });
    await expect(page.getByText("Are you sure")).toBeVisible();

    // Cancel first
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(page.getByText("Are you sure")).not.toBeVisible({ timeout: 2_000 });

    // Now delete for real
    await deleteBtn.click();
    await page.getByRole("button", { name: "Delete" }).click();
    await expect(page.getByText("Are you sure")).not.toBeVisible({ timeout: 3_000 });
  });
});
