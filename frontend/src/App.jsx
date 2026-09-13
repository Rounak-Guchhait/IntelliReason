import { useEffect, useRef, useState } from 'react';
import { API_URL, fetchHealth, streamReason } from './api/client';
import MessageItem from './components/MessageItem';
import Composer from './components/Composer';

const EXAMPLES = [
  'Compute 17% of 640, step by step',
  'Solve x² − 5x + 6 = 0 with full working',
  'What is the probability of rolling two sixes?',
  'Explain why 0.1 + 0.2 ≠ 0.3 in floating point',
  'Debug a loop that never terminates',
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [running, setRunning] = useState(false);
  const [server, setServer] = useState(null);

  useEffect(() => { fetchHealth().then(setServer).catch(() => setServer(null)); }, []);
  useEffect(() => { localStorage.setItem('intellireason.messages', JSON.stringify(messages)); }, [messages]);
  useEffect(() => {
    const saved = localStorage.getItem('intellireason.messages');
    if (saved) { try { setMessages(JSON.parse(saved)); } catch {} }
  }, []);

  const send = async (text) => {
    const question = text.trim();
    if (!question || running) return;
    setRunning(true);
    const qm = { id: 'u' + Date.now(), role: 'user', content: question };
    const id = 'a' + Date.now();
    const am = { id, role: 'assistant', content: '', reason: { phase: 'planning' } };
    setMessages((prev) => [...prev, qm, am]);

    const scroll = () => {
      const el = document.getElementById('messages');
      if (el) el.scrollTop = el.scrollHeight;
    };

    const holder = { error: null };

    const patchReason = (fn) => {
      setMessages((prev) => prev.map((m) =>
        m.id === id ? { ...m, reason: fn({ ...m.reason }) } : m));
      setTimeout(scroll, 0);
    };

    try {
      await streamReason(API_URL, question, (event) => {
        switch (event.type) {
          case 'start':
            patchReason((r) => ({ ...r, phase: 'planning', steps: [] }));
            break;
          case 'step_done':
            patchReason((r) => ({
              ...r, phase: 'solving',
              steps: [...(r.steps || []), event.step],
            }));
            break;
          case 'verification':
            patchReason((r) => ({ ...r, phase: 'verifying', verification: event.verification }));
            break;
          case 'done':
            patchReason(() => ({
              phase: 'done',
              finalAnswer: event.result.final_answer,
              explanation: event.result.explanation,
              verification: event.result.verification,
              steps: event.result.steps,
              durationMs: event.result.duration_ms,
              model: event.result.model,
            }));
            break;
          default: break;
        }
      });
    } catch (err) {
      if (err.name === 'AbortError') return;
      holder.error = String(err.message || err);
      setMessages((prev) => prev.map((m) =>
        m.id === id ? { ...m, reason: { ...(m.reason || {}), phase: 'error', error: holder.error } } : m));
    } finally {
      setRunning(false);
      setInput('');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand"><span className="brand-mark">◈</span><span className="brand-name">IntelliReason</span></div>
        <div className="header-right">
          {server && <span className="server-pill">● {server.model}</span>}
          {running && <button className="stop-btn" onClick={() => /* stop */ null}>Stop</button>}
        </div>
      </header>
      <main className="workspace">
        <div className="pane-tree">
          <h2 className="pane-title">Reasoning tree</h2>
          <div className="pane-scroll">
            {messages.filter((m) => m.role === 'assistant').map((m) =>
              <div className="assistant-block" key={m.id}><MessageItem message={m} /></div>)}
            {messages.filter((m) => m.role === 'assistant').length === 0 &&
              <p className="muted pane-empty">Your reasoning trail will appear here.</p>}
          </div>
        </div>
        <div className="pane-chat">
          <div className="messages" id="messages">
            {messages.length === 0 && (
              <div className="empty-state">
                <p>Ask something that needs real reasoning, and watch IntelliReason plan, solve, verify and explain it.</p>
                <div className="examples">
                  {EXAMPLES.map((e) => <button key={e} onClick={() => setInput(e)}>{e}</button>)}
                </div>
              </div>
            )}
            {messages.map((m) => <MessageItem key={m.id} message={m} />)}
            {running && <div className="typing">reasoning…</div>}
          </div>
          <Composer value={input} onChange={setInput} running={running} onSend={send} />
        </div>
      </main>
    </div>
  );
}