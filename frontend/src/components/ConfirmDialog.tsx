interface ConfirmDialogProps {
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({ title, message, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <div style={styles.overlay} onClick={onCancel}>
      <div style={styles.dialog} onClick={(e) => e.stopPropagation()}>
        <h3 style={styles.title}>{title}</h3>
        <p style={styles.message}>{message}</p>
        <div style={styles.actions}>
          <button onClick={onCancel} style={styles.cancelBtn}>Cancel</button>
          <button onClick={onConfirm} style={styles.confirmBtn}>Delete</button>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.6)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  dialog: {
    background: "#2f2f2f",
    borderRadius: 12,
    padding: "20px 24px",
    width: 360,
    border: "1px solid #444",
  },
  title: {
    fontSize: 16,
    fontWeight: 600,
    marginBottom: 8,
    color: "#e3e3e3",
  },
  message: {
    fontSize: 14,
    color: "#999",
    marginBottom: 20,
    lineHeight: 1.5,
  },
  actions: {
    display: "flex",
    justifyContent: "flex-end",
    gap: 8,
  },
  cancelBtn: {
    padding: "8px 16px",
    background: "transparent",
    border: "1px solid #555",
    borderRadius: 8,
    color: "#e3e3e3",
    cursor: "pointer",
    fontSize: 13,
  },
  confirmBtn: {
    padding: "8px 16px",
    background: "#c53030",
    border: "none",
    borderRadius: 8,
    color: "white",
    cursor: "pointer",
    fontSize: 13,
  },
};
