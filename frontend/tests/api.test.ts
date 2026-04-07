import { describe, it, expect, vi, beforeEach } from "vitest";

vi.stubGlobal("import", { meta: { env: { PUBLIC_API_URL: "http://localhost:8000/api" } } });

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("API service module", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("getChatStreamUrl builds correct URL", async () => {
    const { getChatStreamUrl } = await import("../src/services/api");
    const url = getChatStreamUrl("abc-123");
    expect(url).toContain("/conversations/abc-123/chat");
  });

  it("listConversations calls correct endpoint", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ conversations: [], total: 0 }),
    });

    const { listConversations } = await import("../src/services/api");
    const result = await listConversations();
    expect(result.total).toBe(0);
    expect(result.conversations).toEqual([]);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/conversations?limit=50&offset=0"),
      expect.any(Object),
    );
  });

  it("createConversation sends POST", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({
        id: "new-id",
        title: "New conversation...",
        created_at: "2026-04-07T10:00:00.000Z",
        updated_at: "2026-04-07T10:00:00.000Z",
      }),
    });

    const { createConversation } = await import("../src/services/api");
    const result = await createConversation({ title: "My Chat" });
    expect(result.id).toBe("new-id");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/conversations"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("deleteConversation sends DELETE", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
      json: async () => undefined,
    });

    const { deleteConversation } = await import("../src/services/api");
    await deleteConversation("conv-123");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/conversations/conv-123"),
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({ detail: "Conversation not found" }),
    });

    const { getConversation } = await import("../src/services/api");
    await expect(getConversation("missing-id")).rejects.toThrow("Conversation not found");
  });
});
