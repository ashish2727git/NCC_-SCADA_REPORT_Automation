import { Terminal } from 'lucide-react';

export default function Contact() {
  return (
    <main style={{ marginTop: '100px', padding: '2rem', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div className="glass-panel" style={{ padding: '3rem', width: '100%', maxWidth: '600px', border: '1px solid #00f0ff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem', color: '#00f0ff' }}>
          <Terminal size={24} />
          <h2 className="font-display" style={{ fontSize: '1.5rem', margin: 0 }}>INITIATE_HANDSHAKE</h2>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <input className="chat-input" placeholder="root@domain.com" style={{ width: '100%', boxSizing: 'border-box' }}/>
          <textarea className="chat-input" placeholder="Execute payload..." rows="5" style={{ width: '100%', boxSizing: 'border-box', resize: 'none' }}></textarea>
          <button className="chat-submit" style={{ width: '100%', padding: '1rem', marginTop: '1rem', fontWeight: 'bold' }}>TRANSMIT</button>
        </div>
      </div>
    </main>
  );
}
