export const API_URL =
  (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

export async function fetchHealth() {
  const res = await fetch(`${API_URL}/api/health`);
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}

function nonce() { return (crypto.randomUUID && crypto.randomUUID()) || 'x' + Math.random().toString(36).slice(2); }

/**
 * POST question to /api/stream-reason and call onEvent for each SSE payload.
 * onEvent receives objects: {type, ...}.
 */
export async function streamReason(question, onEvent, opts = {}) {
  const ctrl = opts.signal || new AbortController();
  const res = await fetch(`${API_URL}/api/stream-reason`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history: opts.history || [] }),
    signal: ctrl.signal,
  });
  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => '');
    throw new Error(`server ${res.status}: ${text.slice(0, 200)}`);
  }
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  const handleLine = (line) => {
    const s = line.replace(/^data:\s*/, '').trim();
    if (!s) return;
    let ev;
    try { ev = JSON.parse(s); } catch { return; }
    onEvent(ev);
  };
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const parts = buf.split('\n');
    buf = parts.pop() || '';
    parts.forEach(handleLine);
  }
  if (buf.trim()) handleLine(buf);
}