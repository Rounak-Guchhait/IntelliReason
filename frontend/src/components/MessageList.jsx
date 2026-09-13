import Item from './MessageItem';
export default function MessageList({ messages, running }) {
  if (!messages.length) {
    return (
      <div className="empty">
        Ask something that truly needs step-by-step reasoning and IntelliReason will plan,
        solve with tools, verify, and explain â€” streaming live as it works.
      </div>
    );
  }
  return (
    <div className="messages">
      {messages.map((m) => <Item key={m.id} message={m} />)}
      {running && <div className="typing-dots"><span /><span /><span /></div>}
    </div>
  );
}