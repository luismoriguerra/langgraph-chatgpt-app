import { useState, useRef, useEffect, useCallback } from "react";
import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";
import { createConversation, getChatStreamUrl } from "../services/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatViewProps {
  conversationId: string | null;
  onConversationCreated?: (id: string) => void;
}

export default function ChatView({ conversationId, onConversationCreated }: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeConvId, setActiveConvId] = useState<string | null>(conversationId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setActiveConvId(conversationId);
    if (!conversationId) {
      setMessages([]);
    }
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = useCallback(async (userContent: string) => {
    setError(null);
    setIsLoading(true);

    let convId = activeConvId;

    if (!convId) {
      try {
        const conv = await createConversation({});
        convId = conv.id;
        setActiveConvId(convId);
        onConversationCreated?.(convId);
      } catch (e) {
        setError("Failed to create conversation");
        setIsLoading(false);
        return;
      }
    }

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userContent,
    };
    setMessages((prev) => [...prev, userMsg]);

    const assistantMsg: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content: "",
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
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsg.id
                    ? { ...m, content: m.content + payload.textDelta }
                    : m
                )
              );
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      const msg = e instanceof Error ? e.message : "An error occurred";
      setError(msg);
      setMessages((prev) => prev.filter((m) => m.id !== assistantMsg.id));
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [activeConvId, onConversationCreated]);

  return (
    <div style={styles.container}>
      <div style={styles.messageList}>
        {messages.length === 0 && !isLoading && (
          <div style={styles.empty}>
            <h2 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>How can I help you today?</h2>
            <p style={{ color: "#888", fontSize: 14 }}>Send a message to start a conversation.</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}
        {isLoading && messages[messages.length - 1]?.content === "" && (
          <div style={styles.typing}>
            <span style={styles.dot} />
            <span style={{ ...styles.dot, animationDelay: "0.2s" }} />
            <span style={{ ...styles.dot, animationDelay: "0.4s" }} />
          </div>
        )}
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
