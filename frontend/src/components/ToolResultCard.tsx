import type { CSSProperties } from "react";

export interface ToolResultCardProps {
  toolName: string;
  toolInput: string;
  result?: string | null;
  status: "calling" | "done" | "error";
}

export default function ToolResultCard({
  toolName,
  toolInput,
  result,
  status,
}: ToolResultCardProps) {
  const isError = status === "error" || (result && result.startsWith("Error:"));
  const isCalling = status === "calling";

  const label =
    toolName === "calculate"
      ? "Calculator"
      : toolName === "web_search"
        ? "Web Search"
        : toolName;

  const icon = toolName === "calculate" ? "🧮" : "🔍";

  return (
    <div
      style={{
        ...styles.card,
        ...(isError ? styles.errorCard : {}),
      }}
      role="status"
      aria-live="polite"
      data-tool-name={toolName}
    >
      <div style={styles.header}>
        <span style={styles.icon} aria-hidden>
          {icon}
        </span>
        <span style={styles.label}>{label}</span>
        {isCalling && (
          <span style={styles.dots} aria-hidden>
            <span style={styles.dot} />
            <span style={{ ...styles.dot, animationDelay: "0.2s" }} />
            <span style={{ ...styles.dot, animationDelay: "0.4s" }} />
          </span>
        )}
      </div>

      <div style={styles.inputRow}>
        <span style={styles.inputLabel}>Input:</span>
        <code style={styles.inputValue}>{toolInput}</code>
      </div>

      {result && (
        <div style={{ ...styles.resultRow, ...(isError ? styles.errorText : {}) }}>
          <span style={styles.resultLabel}>{isError ? "Error:" : "Result:"}</span>
          <code style={styles.resultValue}>
            {isError ? result.replace(/^Error:\s*/, "") : result}
          </code>
        </div>
      )}

      <style>{`
        @keyframes toolDotPulse {
          0%, 80%, 100% { opacity: 0.25; transform: scale(0.85); }
          40% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  card: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    padding: "10px 14px",
    marginTop: 4,
    marginBottom: 4,
    borderRadius: 8,
    background: "#2a2a3d",
    border: "1px solid #3a3a5a",
    color: "#e3e3e3",
    fontSize: 13,
    alignSelf: "flex-start",
    maxWidth: "80%",
  },
  errorCard: {
    background: "#3a1a1a",
    border: "1px solid #5a2d2d",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 6,
  },
  icon: {
    fontSize: 14,
    lineHeight: 1,
  },
  label: {
    fontWeight: 600,
    fontSize: 13,
  },
  dots: {
    display: "inline-flex",
    gap: 3,
    alignItems: "center",
    marginLeft: 4,
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: "50%",
    background: "#a8a8a8",
    animation: "toolDotPulse 1.2s ease-in-out infinite both",
  },
  inputRow: {
    display: "flex",
    gap: 6,
    alignItems: "baseline",
  },
  inputLabel: {
    color: "#888",
    fontSize: 12,
    flexShrink: 0,
  },
  inputValue: {
    background: "#1a1a2e",
    padding: "2px 6px",
    borderRadius: 4,
    fontSize: 12,
    wordBreak: "break-all",
  },
  resultRow: {
    display: "flex",
    gap: 6,
    alignItems: "baseline",
  },
  errorText: {
    color: "#cf6f6f",
  },
  resultLabel: {
    color: "#888",
    fontSize: 12,
    flexShrink: 0,
  },
  resultValue: {
    background: "#1a1a2e",
    padding: "2px 6px",
    borderRadius: 4,
    fontSize: 13,
    fontWeight: 600,
    color: "#a0d995",
    wordBreak: "break-all",
  },
};
