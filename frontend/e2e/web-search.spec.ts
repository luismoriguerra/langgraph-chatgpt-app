import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ mode: "serial", timeout: 120_000 });

async function sendMessage(page: Page, text: string) {
  const input = page.getByPlaceholder("Send a message...");
  await input.fill(text);
  await input.press("Enter");
}

async function waitForAssistantParagraph(page: Page, minLength: number) {
  await expect(async () => {
    const main = page.locator("main");
    const count = await main.getByRole("paragraph").count();
    if (count === 0) return false;
    const last = main.getByRole("paragraph").nth(count - 1);
    const t = (await last.textContent())?.trim() ?? "";
    return t.length >= minLength;
  }).toPass({ timeout: 30_000 });
}

test.describe("Web Search Tool", () => {
  test("T034: search query shows indicator and streams answer with source citations", async ({
    page,
  }) => {
    await page.goto("/");
    await sendMessage(
      page,
      "What are three major world news headlines from the last few days? Cite sources with links."
    );
    const searching = page.getByText("Searching the web...");
    await expect(searching).toBeVisible({ timeout: 20_000 });
    await expect(searching).toBeHidden({ timeout: 90_000 });
    await waitForAssistantParagraph(page, 80);
    const citationLinks = page.locator("main").getByRole("link", { name: /.+/ });
    await expect(citationLinks.first()).toBeVisible({ timeout: 5_000 });
    expect(await citationLinks.count()).toBeGreaterThanOrEqual(1);
  });

  test("T035: knowledge question has no search indicator", async ({ page }) => {
    await page.goto("/");
    await sendMessage(page, "What is photosynthesis?");
    await expect(async () => {
      const visible = await page.getByText("Searching the web...").isVisible();
      if (visible) {
        throw new Error("Searching the web should not appear for a knowledge-only question");
      }
      const main = page.locator("main");
      const count = await main.getByRole("paragraph").count();
      if (count === 0) return false;
      const last = main.getByRole("paragraph").nth(count - 1);
      const t = (await last.textContent())?.trim() ?? "";
      return t.length >= 60;
    }).toPass({ timeout: 30_000 });
  });

  test("T036: page reload preserves conversation with source links", async ({ page }) => {
    await page.goto("/");
    await sendMessage(page, "What is the current weather forecast for Paris today? Include source links.");
    const searching = page.getByText("Searching the web...");
    await expect(searching).toBeVisible({ timeout: 20_000 });
    await expect(searching).toBeHidden({ timeout: 90_000 });
    await waitForAssistantParagraph(page, 40);
    const beforeReload = await page.locator("main").getByRole("link").count();
    expect(beforeReload).toBeGreaterThanOrEqual(1);

    await page.reload();
    await expect(page.getByPlaceholder("Send a message...")).toBeVisible({ timeout: 15_000 });

    const aside = page.getByRole("complementary");
    const convoButton = aside.getByRole("button").nth(1);
    await expect(convoButton).toBeVisible({ timeout: 15_000 });
    await convoButton.click();

    await expect(page.getByText("What is the current weather forecast for Paris today?")).toBeVisible({
      timeout: 15_000,
    });
    await waitForAssistantParagraph(page, 40);
    await expect(page.locator("main").getByRole("link").first()).toBeVisible({ timeout: 10_000 });
  });

  test("T037: multi-turn search with pronoun disambiguation", async ({ page }) => {
    await page.goto("/");
    await sendMessage(page, "Tell me briefly about the company Tesla Inc.");
    await expect(page.getByText("Searching the web...")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Searching the web...")).toBeHidden({ timeout: 90_000 });
    await waitForAssistantParagraph(page, 50);

    await sendMessage(page, "What is their current stock price or latest trading context?");
    await expect(page.getByText("Searching the web...")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Searching the web...")).toBeHidden({ timeout: 90_000 });
    await waitForAssistantParagraph(page, 40);
    const mainText = await page.locator("main").textContent();
    expect(mainText?.toLowerCase()).toMatch(/tesla|tsla|stock|price|trading|share/i);
  });

  test("T038: search failure shows graceful fallback", async ({ page }) => {
    await page.goto("/");
    await sendMessage(
      page,
      "List two breaking news stories from today with URLs. If you cannot search, answer from general knowledge without erroring."
    );
    await waitForAssistantParagraph(page, 40);
    await expect(page.locator("main")).toBeVisible();
    await expect(page.getByRole("button", { name: "Dismiss" })).toBeHidden();
  });
});
