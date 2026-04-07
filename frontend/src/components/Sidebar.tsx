import { useState, useEffect, useCallback } from "react";
import { listConversations } from "../services/api";
import type { Conversation } from "../types";

interface SidebarProps {
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  refreshKey?: number;
}

export default function Sidebar({ activeId, onSelect, onNewChat, refreshKey }: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const refresh = useCallback(async () => {
    try {
      const data = await listConversations();
      setConversations(data.conversations);
    } catch {
      // silent fail on sidebar load
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, refreshKey]);

  return (
    <div style={styles.container}>
      <button onClick={onNewChat} style={styles.newChatBtn}>
        + New Chat
      </button>
      <div style={styles.list}>
        {conversations.map((conv) => (
          <button
            key={conv.id}
            onClick={() => onSelect(conv.id)}
            style={{
              ...styles.item,
              background: conv.id === activeId ? "#2f2f2f" : "transparent",
            }}
          >
            {conv.title}
          </button>
        ))}
        {conversations.length === 0 && (
          <div style={styles.empty}>No conversations yet</div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    padding: 8,
  },
  newChatBtn: {
    padding: "10px 16px",
    background: "#2f2f2f",
    color: "#e3e3e3",
    border: "1px solid #444",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 14,
    marginBottom: 12,
    textAlign: "left",
    transition: "background 0.15s",
  },
  list: {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  item: {
    padding: "10px 12px",
    border: "none",
    borderRadius: 8,
    color: "#e3e3e3",
    cursor: "pointer",
    fontSize: 13,
    textAlign: "left",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    transition: "background 0.15s",
  },
  empty: {
    color: "#666",
    fontSize: 13,
    padding: "12px 8px",
  },
};
