import type { CSSProperties } from "react";

interface SearchIndicatorProps {
  visible: boolean;
}

export default function SearchIndicator({ visible }: SearchIndicatorProps) {
  if (!visible) return null;

  return (
    <div style={styles.wrap} role="status" aria-live="polite">
      <span style={styles.icon} aria-hidden>
        🔍
      </span>
      <span style={styles.label}>Searching the web...</span>
      <span style={styles.dots} aria-hidden>
        <span style={styles.dot} />
        <span style={{ ...styles.dot, animationDelay: "0.2s" }} />
        <span style={{ ...styles.dot, animationDelay: "0.4s" }} />
      </span>
      <style>{`
        @keyframes searchDotPulse {
          0%, 80%, 100% { opacity: 0.25; transform: scale(0.85); }
          40% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  wrap: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 16px",
    marginTop: 4,
    borderRadius: 8,
    background: "#2f2f2f",
    color: "#e3e3e3",
    fontSize: 14,
    alignSelf: "flex-start",
  },
  icon: {
    fontSize: 16,
    lineHeight: 1,
  },
  label: {
    flexShrink: 0,
  },
  dots: {
    display: "inline-flex",
    gap: 4,
    alignItems: "center",
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    background: "#a8a8a8",
    animation: "searchDotPulse 1.2s ease-in-out infinite both",
  },
};
