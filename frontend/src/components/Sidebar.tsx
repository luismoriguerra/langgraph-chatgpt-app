import { useState, useEffect, useCallback } from "react";
import { listConversations, deleteConversation } from "../services/api";
import type { Conversation } from "../types";
import ConfirmDialog from "./ConfirmDialog";

interface SidebarProps {
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDeleted?: (id: string) => void;
  refreshKey?: number;
}

export default function Sidebar({ activeId, onSelect, onNewChat, onDeleted, refreshKey }: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<Conversation | null>(null);

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

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteConversation(deleteTarget.id);
      setConversations((prev) => prev.filter((c) => c.id !== deleteTarget.id));
      onDeleted?.(deleteTarget.id);
    } catch {
      // silent fail
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <div style={styles.container}>
      <button onClick={onNewChat} style={styles.newChatBtn}>
        + New Chat
      </button>

      <div style={styles.list}>
        {conversations.map((conv) => (
          <div
            key={conv.id}
            style={{
              ...styles.item,
              background: conv.id === activeId ? "#2f2f2f" : "transparent",
            }}
          >
            <button
              onClick={() => onSelect(conv.id)}
              style={styles.itemTitle}
            >
              {conv.title}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setDeleteTarget(conv);
              }}
              style={styles.deleteBtn}
              title="Delete conversation"
            >
              ×
            </button>
          </div>
        ))}
        {conversations.length === 0 && (
          <div style={styles.empty}>No conversations yet</div>
        )}
      </div>

      {deleteTarget && (
        <ConfirmDialog
          title="Delete conversation"
          message={`Are you sure you want to delete "${deleteTarget.title}"? This cannot be undone.`}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
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
    textAlign: "left" as const,
    transition: "background 0.15s",
  },
  list: {
    flex: 1,
    overflowY: "auto" as const,
    display: "flex",
    flexDirection: "column" as const,
    gap: 2,
  },
  item: {
    display: "flex",
    alignItems: "center",
    borderRadius: 8,
    transition: "background 0.15s",
    position: "relative" as const,
  },
  itemTitle: {
    flex: 1,
    padding: "10px 12px",
    border: "none",
    background: "transparent",
    color: "#e3e3e3",
    cursor: "pointer",
    fontSize: 13,
    textAlign: "left" as const,
    whiteSpace: "nowrap" as const,
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  deleteBtn: {
    background: "transparent",
    border: "none",
    color: "#666",
    cursor: "pointer",
    fontSize: 18,
    padding: "4px 10px",
    borderRadius: 4,
    flexShrink: 0,
    lineHeight: 1,
  },
  empty: {
    color: "#666",
    fontSize: 13,
    padding: "12px 8px",
  },
};
