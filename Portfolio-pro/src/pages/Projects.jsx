import '../components/V6Application.css';

export default function Projects() {
  return (
    <main style={{ marginTop: '100px', padding: '2rem', height: '100vh', overflowY: 'auto' }}>
      <h1 className="font-display massive-headline" style={{ fontSize: '5rem', marginBottom: '2rem' }}>THE ARCHIVES //</h1>
      <p className="subtitle" style={{ marginBottom: '4rem' }}>A comprehensive breakdown of all technical systems and interfaces built to date.</p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
        <div className="glass-panel" style={{ padding: '3rem', display: 'flex', gap: '2rem' }}>
           <img src="/img1.jpg" alt="Nexus Sync" style={{ width: '40%', borderRadius: '8px', objectFit: 'cover' }}/>
           <div>
             <h2 className="font-display text-cyan" style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Nexus Sync Pro</h2>
             <p style={{ fontSize: '1.2rem', color: '#ccc', marginBottom: '2rem', lineHeight: '1.6' }}>
               An orchestrator designed to establish robust sync states natively on Windows using Python automation and PyInstaller binaries.
             </p>
             <div className="tech-stack">
                <span className="tech-badge">Python</span>
                <span className="tech-badge">OS API</span>
                <span className="tech-badge">PyInstaller</span>
             </div>
           </div>
        </div>

        <div className="glass-panel" style={{ padding: '3rem', display: 'flex', gap: '2rem' }}>
           <img src="/img2.jpg" alt="SquadSync" style={{ width: '40%', borderRadius: '8px', objectFit: 'cover' }}/>
           <div>
             <h2 className="font-display text-cyan" style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>SquadSync</h2>
             <p style={{ fontSize: '1.2rem', color: '#ccc', marginBottom: '2rem', lineHeight: '1.6' }}>
               A real-time WebRTC communications terminal for competitive esports, using Supabase for low-latency backend synchronization.
             </p>
             <div className="tech-stack">
                <span className="tech-badge">React 19</span>
                <span className="tech-badge">Supabase</span>
                <span className="tech-badge">Zustand</span>
             </div>
           </div>
        </div>

        <div className="glass-panel" style={{ padding: '3rem', display: 'flex', gap: '2rem' }}>
           <img src="/img3.jpg" alt="ZeroG Automator" style={{ width: '40%', borderRadius: '8px', objectFit: 'cover' }}/>
           <div>
             <h2 className="font-display text-cyan" style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>ZeroG Automator</h2>
             <p style={{ fontSize: '1.2rem', color: '#ccc', marginBottom: '2rem', lineHeight: '1.6' }}>
               Advanced Chrome automation extension providing real-time CV processing for direct DOM injection in restricted environments.
             </p>
             <div className="tech-stack">
                <span className="tech-badge">JavaScript</span>
                <span className="tech-badge">Chrome Extensions API</span>
                <span className="tech-badge">Playwright</span>
             </div>
           </div>
        </div>
      </div>
    </main>
  );
}
