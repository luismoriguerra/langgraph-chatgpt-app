import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import ChatView from "../src/components/ChatView";
import * as api from "../src/services/api";

vi.mock("../src/services/api", () => ({
  getConversation: vi.fn(),
  createConversation: vi.fn(),
  getChatStreamUrl: vi.fn((id: string) => `http://test/api/conversations/${id}/chat`),
}));

const originalFetch = globalThis.fetch;

function sseResponse(chunks: string[]) {
  const encoder = new TextEncoder();
  let i = 0;
  return {
    ok: true,
    body: new ReadableStream<Uint8Array>({
      pull(controller) {
        if (i >= chunks.length) {
          controller.close();
          return;
        }
        controller.enqueue(encoder.encode(chunks[i]));
        i += 1;
      },
    }),
  } as Response;
}

function sseResponseToolStartThenEndDelayed() {
  const encoder = new TextEncoder();
  let step = 0;
  return {
    ok: true,
    body: new ReadableStream<Uint8Array>({
      async pull(controller) {
        if (step === 0) {
          controller.enqueue(encoder.encode('data: {"type":"tool-start"}\n'));
          step = 1;
          return;
        }
        if (step === 1) {
          await new Promise<void>((r) => setTimeout(r, 30));
          controller.enqueue(encoder.encode('data: {"type":"tool-end"}\n'));
          step = 2;
          controller.close();
        }
      },
    }),
  } as Response;
}

describe("ChatView SSE / isSearching", () => {
  const conv = {
    id: "conv-1",
    title: "T",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    messages: [] as { id: string; role: "user" | "assistant"; content: string; created_at: string }[],
  };

  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
    vi.clearAllMocks();
    vi.mocked(api.getConversation).mockResolvedValue(conv);
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("starts with isSearching false (no search indicator)", async () => {
    render(<ChatView conversationId="conv-1" />);
    await waitFor(() => expect(api.getConversation).toHaveBeenCalled());
    expect(screen.queryByText("Searching the web...")).toBeNull();
  });

  it("shows SearchIndicator after tool-start SSE event", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      sseResponse(['data: {"type":"tool-start"}\n'])
    );

    render(<ChatView conversationId="conv-1" />);
    await waitFor(() => expect(api.getConversation).toHaveBeenCalled());

    fireEvent.change(screen.getByPlaceholderText("Send a message..."), {
      target: { value: "query" },
    });
    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => expect(screen.getByText("Searching the web...")).toBeTruthy());
  });

  it("hides SearchIndicator after tool-end SSE event", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(sseResponseToolStartThenEndDelayed());

    render(<ChatView conversationId="conv-1" />);
    await waitFor(() => expect(api.getConversation).toHaveBeenCalled());

    fireEvent.change(screen.getByPlaceholderText("Send a message..."), {
      target: { value: "query" },
    });
    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => expect(screen.getByText("Searching the web...")).toBeTruthy());
    await waitFor(() => expect(screen.queryByText("Searching the web...")).toBeNull());
  });
});

describe("ChatView conversation reload / tool_invocations", () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
    vi.clearAllMocks();
  });

  it("maps tool_invocations from getConversation response into message state", async () => {
    vi.mocked(api.getConversation).mockResolvedValue({
      id: "conv-t",
      title: "T",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      messages: [
        {
          id: "m1",
          role: "user",
          content: "Hi",
          created_at: "2026-01-01T00:00:01Z",
        },
        {
          id: "m2",
          role: "assistant",
          content: "Hello",
          created_at: "2026-01-01T00:00:02Z",
          tool_invocations: [
            {
              id: "t1",
              tool_name: "duckduckgo_results_search",
              tool_input: "{}",
              tool_output: [{ title: "T", snippet: "S", url: "https://x" }],
              created_at: "2026-01-01T00:00:03Z",
            },
          ],
        },
      ],
    });

    const { container } = render(<ChatView conversationId="conv-t" />);

    await waitFor(() => {
      expect(api.getConversation).toHaveBeenCalledWith("conv-t");
    });

    await waitFor(() => {
      const counts = [...container.querySelectorAll("[data-tool-invocation-count]")].map((el) =>
        el.getAttribute("data-tool-invocation-count")
      );
      expect(counts).toEqual(["0", "1"]);
    });
  });

  it("uses empty tool_invocations when API omits the field", async () => {
    vi.mocked(api.getConversation).mockResolvedValue({
      id: "conv-u",
      title: "T",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      messages: [
        {
          id: "m1",
          role: "assistant",
          content: "No tools",
          created_at: "2026-01-01T00:00:02Z",
        },
      ],
    });

    const { container } = render(<ChatView conversationId="conv-u" />);

    await waitFor(() => {
      expect(container.querySelector('[data-tool-invocation-count="0"]')).not.toBeNull();
    });
  });
});
