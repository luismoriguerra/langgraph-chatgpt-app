import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/cjs/styles/prism";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
}

export default function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";

  if (isUser) {
    return (
      <div style={styles.wrapper}>
        <div style={{ ...styles.bubble, ...styles.userBubble }}>{content}</div>
      </div>
    );
  }

  return (
    <div style={styles.wrapper}>
      <div style={{ ...styles.bubble, ...styles.assistantBubble }}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || "");
              const codeString = String(children).replace(/\n$/, "");

              if (match) {
                return (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match[1]}
                    PreTag="div"
                    customStyle={{
                      margin: "8px 0",
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                  >
                    {codeString}
                  </SyntaxHighlighter>
                );
              }

              return (
                <code
                  style={{
                    background: "#1a1a2e",
                    padding: "2px 6px",
                    borderRadius: 4,
                    fontSize: 13,
                  }}
                  {...props}
                >
                  {children}
                </code>
              );
            },
            p({ children }) {
              return <p style={{ margin: "8px 0", lineHeight: 1.6 }}>{children}</p>;
            },
            ul({ children }) {
              return <ul style={{ margin: "8px 0", paddingLeft: 20 }}>{children}</ul>;
            },
            ol({ children }) {
              return <ol style={{ margin: "8px 0", paddingLeft: 20 }}>{children}</ol>;
            },
            a({ children, href }) {
              return (
                <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#7eb8ff" }}>
                  {children}
                </a>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: "flex",
    padding: "8px 0",
  },
  bubble: {
    maxWidth: "80%",
    padding: "10px 16px",
    borderRadius: 12,
    fontSize: 15,
    lineHeight: 1.5,
    wordBreak: "break-word",
  },
  userBubble: {
    marginLeft: "auto",
    background: "#2f5f3f",
    color: "#e3e3e3",
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    background: "#2f2f2f",
    color: "#e3e3e3",
    borderBottomLeftRadius: 4,
  },
};
