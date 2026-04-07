import type {
  Conversation,
  ConversationListResponse,
  ConversationWithMessages,
  CreateConversationRequest,
  UpdateConversationRequest,
} from "../types";

const API_URL = import.meta.env.PUBLIC_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function listConversations(
  limit = 50,
  offset = 0
): Promise<ConversationListResponse> {
  return request(`/conversations?limit=${limit}&offset=${offset}`);
}

export async function getConversation(id: string): Promise<ConversationWithMessages> {
  return request(`/conversations/${id}`);
}

export async function createConversation(
  data: CreateConversationRequest = {}
): Promise<Conversation> {
  return request("/conversations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteConversation(id: string): Promise<void> {
  return request(`/conversations/${id}`, { method: "DELETE" });
}

export async function updateTitle(id: string, data: UpdateConversationRequest): Promise<Conversation> {
  return request(`/conversations/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function getChatStreamUrl(conversationId: string): string {
  return `${API_URL}/conversations/${conversationId}/chat`;
}
