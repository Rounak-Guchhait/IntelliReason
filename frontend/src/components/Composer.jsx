export default function Composer({ value, onChange, disabled, onSend }) {
  const submit = (e) => {
    e.preventDefault();
    const t = value.trim();
    if (!t || disabled) return;
    onSend(t);
    onChange('');
  };

  return (
    <form className="composer" onSubmit={submit}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submit(e);
          }
        }}
        placeholder="Ask a question that genuinely needs reasoning…"
        rows={3}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !value.trim()} aria-label="Send">
        <span className="send-arrow">➤</span>
      </button>
    </form>
  );
}