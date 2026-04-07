import { describe, it, expect } from "vitest";
import type {
  Conversation,
  Message,
  ConversationWithMessages,
  ConversationListResponse,
  SendMessageRequest,
} from "../src/types";

describe("TypeScript interfaces", () => {
  it("Conversation object matches expected shape", () => {
    const conv: Conversation = {
      id: "550e8400-e29b-41d4-a716-446655440000",
      title: "Test Chat",
      created_at: "2026-04-07T10:00:00.000Z",
      updated_at: "2026-04-07T12:30:00.000Z",
    };
    expect(conv.id).toBeDefined();
    expect(conv.title).toBe("Test Chat");
  });

  it("Message object has role constraint at runtime", () => {
    const userMsg: Message = {
      id: "msg-1",
      role: "user",
      content: "Hello",
      created_at: "2026-04-07T10:00:00.000Z",
    };
    const assistantMsg: Message = {
      id: "msg-2",
      role: "assistant",
      content: "Hi there!",
      created_at: "2026-04-07T10:00:01.000Z",
    };
    expect(userMsg.role).toBe("user");
    expect(assistantMsg.role).toBe("assistant");
  });

  it("ConversationWithMessages includes messages array", () => {
    const conv: ConversationWithMessages = {
      id: "conv-1",
      title: "Test",
      created_at: "2026-04-07T10:00:00.000Z",
      updated_at: "2026-04-07T10:00:00.000Z",
      messages: [
        {
          id: "msg-1",
          role: "user",
          content: "Hello",
          created_at: "2026-04-07T10:00:00.000Z",
        },
      ],
    };
    expect(conv.messages).toHaveLength(1);
    expect(conv.messages[0]?.role).toBe("user");
  });

  it("ConversationListResponse has conversations and total", () => {
    const resp: ConversationListResponse = {
      conversations: [],
      total: 0,
    };
    expect(resp.conversations).toEqual([]);
    expect(resp.total).toBe(0);
  });

  it("SendMessageRequest requires message field", () => {
    const req: SendMessageRequest = { message: "Test message" };
    expect(req.message).toBe("Test message");
  });
});
