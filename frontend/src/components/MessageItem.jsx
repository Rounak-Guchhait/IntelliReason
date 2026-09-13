export default function MessageItem({ message }) {
  const isUser = message.role === 'user';
  const r = message.reason;
  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="avatar">{isUser ? 'You' : 'IR'}</div>
      <div className="message-body">
        {isUser ? (
          <div className="bubble bubble-user">{message.content}</div>
        ) : (
          <div className="bubble bubble-assistant">
            <div className="phase-line">
              <span className="phase-tag">{r?.phase || 'queued'}</span>
              {r?.model && <span className="model-tag">{r.model}</span>}
            </div>
            {r?.steps?.map((s, i) => (
              <div className="step" key={i}>
                <div className="step-head">
                  <span className="step-num">{i + 1}</span>
                  <span className="step-desc">{s.description}</span>
                </div>
                <details className="tools">
                  <summary>tools ({s.tool_calls?.length || 0})</summary>
                  {s.tool_calls?.map((t, j) => (
                    <div className="tool-row" key={j}>
                      <span className="tool-name">{t.name}</span>
                      <pre className="tool-args">{JSON.stringify(t.args)}</pre>
                      {t.output && <pre className="tool-out">{t.output}</pre>}
                    </div>
                  ))}
                </details>
                <div className="step-sol">{s.solution}</div>
              </div>
            ))}
            {r?.verification && (
              <div className={`verdict ${r.verification.verdict}`}>
                {r.verification.verdict}{r.verification.notes?.map((n, i) => <div key={i}>{n}</div>)}
              </div>
            )}
            {r?.phase === 'waiting' && <div className="pulse">thinking…</div>}
            {message.error && <div className="error-text">{message.error}</div>}
          </div>
        )}
      </div>
    </div>
  );
}