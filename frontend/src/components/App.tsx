import { useState, useCallback } from "react";
import Sidebar from "./Sidebar";
import ChatView from "./ChatView";
import { getConversation } from "../services/api";
import type { Message } from "../types";

export default function App() {
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSelect = useCallback(async (id: string) => {
    setActiveConvId(id);
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveConvId(null);
  }, []);

  const handleConversationCreated = useCallback((id: string) => {
    setActiveConvId(id);
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <div style={styles.shell}>
      <aside style={styles.sidebar}>
        <Sidebar
          activeId={activeConvId}
          onSelect={handleSelect}
          onNewChat={handleNewChat}
          refreshKey={refreshKey}
        />
      </aside>
      <main style={styles.content}>
        <ChatView
          conversationId={activeConvId}
          onConversationCreated={handleConversationCreated}
        />
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  shell: {
    display: "flex",
    height: "100vh",
    background: "#212121",
    color: "#e3e3e3",
  },
  sidebar: {
    width: 260,
    flexShrink: 0,
    background: "#171717",
    borderRight: "1px solid #2f2f2f",
  },
  content: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
};
