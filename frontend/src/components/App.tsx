import { useState, useCallback } from "react";
import Sidebar from "./Sidebar";
import ChatView from "./ChatView";

export default function App() {
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSelect = useCallback((id: string) => {
    setActiveConvId(id);
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveConvId(null);
  }, []);

  const handleConversationCreated = useCallback((id: string) => {
    setActiveConvId(id);
    setRefreshKey((k) => k + 1);
  }, []);

  const handleDeleted = useCallback((id: string) => {
    if (id === activeConvId) {
      setActiveConvId(null);
    }
  }, [activeConvId]);

  return (
    <div style={styles.shell}>
      <aside style={styles.sidebar}>
        <Sidebar
          activeId={activeConvId}
          onSelect={handleSelect}
          onNewChat={handleNewChat}
          onDeleted={handleDeleted}
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
