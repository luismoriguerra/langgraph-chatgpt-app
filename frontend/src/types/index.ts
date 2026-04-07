export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  title: string;
  snippet: string;
  url: string;
}

export interface ToolInvocation {
  id: string;
  tool_name: string;
  tool_input: string;
  tool_output: Source[];
  tool_result?: string | null;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  tool_invocations?: ToolInvocation[];
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export interface SendMessageRequest {
  message: string;
}

export interface CreateConversationRequest {
  title?: string;
}

export interface UpdateConversationRequest {
  title: string;
}
