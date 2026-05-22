export default function About() {
  return (
    <main style={{ marginTop: '100px', padding: '2rem', height: '100vh' }}>
      <div className="glass-panel" style={{ padding: '4rem', maxWidth: '800px', margin: '0 auto' }}>
        <h1 className="font-display text-cyan" style={{ fontSize: '4rem', marginBottom: '2rem' }}>0xFF_ARCHITECT</h1>
        <p style={{ fontSize: '1.2rem', color: '#ccc', lineHeight: '1.8', marginBottom: '2rem' }}>
          I am a systems engineer and creative developer. I specialize in bridging the gap between raw backend automation (Python/OS internals) and high-fidelity frontend rendering (React/WebGL). 
        </p>
        <p style={{ fontSize: '1.2rem', color: '#ccc', lineHeight: '1.8' }}>
          My core philosophy is "Functional Intelligence." I believe visually striking interfaces mean nothing if they aren't backed by robust data architectures and AI-native usability paradigms.
        </p>
      </div>
    </main>
  );
}
