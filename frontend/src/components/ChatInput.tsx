import { useState, useRef, type KeyboardEvent, type FormEvent } from "react";

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSubmit, isLoading }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.inputWrapper}>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Send a message..."
          rows={1}
          maxLength={10000}
          disabled={isLoading}
          style={styles.textarea}
        />
        <button
          type="submit"
          disabled={!value.trim() || isLoading}
          style={{
            ...styles.button,
            opacity: !value.trim() || isLoading ? 0.4 : 1,
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 2L11 13" />
            <path d="M22 2L15 22L11 13L2 9L22 2Z" />
          </svg>
        </button>
      </div>
      <div style={styles.charCount}>
        {value.length > 0 && <span>{value.length.toLocaleString()} / 10,000</span>}
      </div>
    </form>
  );
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    padding: "12px 16px 16px",
    borderTop: "1px solid #2f2f2f",
    background: "#212121",
  },
  inputWrapper: {
    display: "flex",
    alignItems: "flex-end",
    gap: 8,
    background: "#2f2f2f",
    borderRadius: 12,
    padding: "8px 12px",
    border: "1px solid #444",
  },
  textarea: {
    flex: 1,
    background: "transparent",
    border: "none",
    outline: "none",
    color: "#e3e3e3",
    fontSize: 15,
    fontFamily: "inherit",
    resize: "none",
    lineHeight: "1.5",
    maxHeight: 200,
  },
  button: {
    background: "white",
    color: "#212121",
    border: "none",
    borderRadius: 8,
    width: 32,
    height: 32,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    flexShrink: 0,
  },
  charCount: {
    textAlign: "right",
    fontSize: 11,
    color: "#666",
    marginTop: 4,
    paddingRight: 4,
    minHeight: 16,
  },
};
