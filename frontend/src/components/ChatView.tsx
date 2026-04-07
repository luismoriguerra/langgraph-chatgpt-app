import { useState, useRef, useEffect, useCallback } from "react";
import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";
import SearchIndicator from "./SearchIndicator";
import ToolResultCard from "./ToolResultCard";
import { createConversation, getConversation, getChatStreamUrl } from "../services/api";
import type { Message, Source } from "../types";

interface ActiveToolCall {
  toolName: string;
  toolInput: string;
  result?: string;
  status: "calling" | "done" | "error";
}

interface ChatViewProps {
  conversationId: string | null;
  onConversationCreated?: (id: string) => void;
}

export default function ChatView({ conversationId, onConversationCreated }: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [activeToolCalls, setActiveToolCalls] = useState<ActiveToolCall[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activeConvId, setActiveConvId] = useState<string | null>(conversationId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const justCreatedRef = useRef<string | null>(null);

  useEffect(() => {
    setActiveConvId(conversationId);
    setError(null);
    if (!conversationId) {
      setMessages([]);
      return;
    }
    if (justCreatedRef.current === conversationId) {
      justCreatedRef.current = null;
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const conv = await getConversation(conversationId);
        if (cancelled) return;
        setMessages(
          conv.messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            created_at: m.created_at,
            tool_invocations: m.tool_invocations || [],
          }))
        );
      } catch {
        if (!cancelled) setError("Failed to load conversation");
      }
    })();
    return () => { cancelled = true; };
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = useCallback(async (userContent: string) => {
    setError(null);
    setIsSearching(false);
    setSources([]);
    setActiveToolCalls([]);
    setIsLoading(true);

    let convId = activeConvId;

    if (!convId) {
      try {
        const conv = await createConversation({});
        convId = conv.id;
        justCreatedRef.current = convId;
        setActiveConvId(convId);
        onConversationCreated?.(convId);
      } catch {
        setError("Failed to create conversation");
        setIsLoading(false);
        return;
      }
    }

    const now = new Date().toISOString();
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userContent,
      created_at: now,
    };
    setMessages((prev) => [...prev, userMsg]);

    const assistantMsg: Message = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content: "",
      created_at: now,
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      abortRef.current = new AbortController();
      const res = await fetch(getChatStreamUrl(convId), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userContent }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(err.detail);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No response body");

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const payload = JSON.parse(line.slice(6));
            if (payload.type === "text-delta" && payload.textDelta) {
              setIsSearching(false);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsg.id
                    ? { ...m, content: m.content + payload.textDelta }
                    : m
                )
              );
            }
            if (payload.type === "tool-start") {
              setIsSearching(true);
              setActiveToolCalls((prev) => [
                ...prev,
                {
                  toolName: payload.toolName,
                  toolInput: payload.toolInput,
                  status: "calling",
                },
              ]);
            }
            if (payload.type === "tool-result") {
              const isError = payload.result?.startsWith("Error:");
              setActiveToolCalls((prev) =>
                prev.map((tc) =>
                  tc.toolName === payload.toolName && tc.status === "calling"
                    ? { ...tc, result: payload.result, status: isError ? "error" : "done" }
                    : tc
                )
              );
            }
            if (payload.type === "sources") {
              setSources(payload.sources || []);
            }
          } catch {
            continue;
          }
        }
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      const msg = e instanceof Error ? e.message : "An error occurred";
      setError(msg);
      setMessages((prev) =>
        prev.filter((m) => {
          if (m.id === assistantMsg.id && !m.content) return false;
          return true;
        })
      );
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [activeConvId, onConversationCreated]);

  return (
    <div
      style={styles.container}
      aria-busy={isLoading || isSearching}
      data-source-count={sources.length}
    >
      <div style={styles.messageList}>
        {messages.length === 0 && !isLoading && (
          <div style={styles.empty}>
            <h2 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>How can I help you today?</h2>
            <p style={{ color: "#888", fontSize: 14 }}>Send a message to start a conversation.</p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{ display: "contents" }}
            data-tool-invocation-count={(msg.tool_invocations ?? []).length}
          >
            {msg.role === "assistant" &&
              (msg.tool_invocations ?? []).map((inv, idx) => (
                <ToolResultCard
                  key={`inv-${inv.id ?? idx}`}
                  toolName={inv.tool_name}
                  toolInput={inv.tool_input}
                  result={inv.tool_result ?? null}
                  status={inv.tool_result?.startsWith("Error:") ? "error" : "done"}
                />
              ))}
            <MessageBubble role={msg.role} content={msg.content} />
          </div>
        ))}
        {isLoading && messages[messages.length - 1]?.content === "" && (
          <div style={styles.typing}>
            <span style={styles.dot} />
            <span style={{ ...styles.dot, animationDelay: "0.2s" }} />
            <span style={{ ...styles.dot, animationDelay: "0.4s" }} />
          </div>
        )}
        {activeToolCalls.map((tc, idx) => (
          <ToolResultCard
            key={`active-${tc.toolName}-${idx}`}
            toolName={tc.toolName}
            toolInput={tc.toolInput}
            result={tc.result}
            status={tc.status}
          />
        ))}
        <SearchIndicator visible={isSearching} />
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div style={styles.errorBar}>
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            style={styles.retryBtn}
          >
            Dismiss
          </button>
        </div>
      )}

      <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />

      <style>{`
        @keyframes blink {
          0%, 80%, 100% { opacity: 0.3; }
          40% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    background: "#212121",
  },
  messageList: {
    flex: 1,
    overflowY: "auto",
    padding: "16px 24px",
    display: "flex",
    flexDirection: "column",
  },
  empty: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    color: "#e3e3e3",
  },
  typing: {
    display: "flex",
    gap: 4,
    padding: "12px 16px",
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: "#888",
    animation: "blink 1.4s infinite both",
  },
  errorBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "8px 16px",
    background: "#3a1a1a",
    color: "#cf6f6f",
    fontSize: 13,
    borderTop: "1px solid #5a2d2d",
  },
  retryBtn: {
    background: "transparent",
    border: "1px solid #5a2d2d",
    color: "#cf6f6f",
    padding: "4px 12px",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 12,
  },
};
