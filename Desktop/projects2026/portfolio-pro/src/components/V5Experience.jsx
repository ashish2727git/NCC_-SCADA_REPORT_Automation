import MagneticNode from './MagneticNode';
import './V5Experience.css';

export default function V5Experience() {
  return (
    <div className="v5-container">
      <header className="v5-header">
        <MagneticNode>
          <a href="#" className="omni-link">STUDIO.OMNI</a>
        </MagneticNode>
        <MagneticNode>
          <a href="#" className="omni-link">Say Hello</a>
        </MagneticNode>
      </header>

      <section className="v5-hero">
        <div className="hero-typography">
          <h1 className="hero-line mix-blend-text">DIGITAL</h1>
          <h1 className="hero-line text-outline">NIRVANA</h1>
        </div>
      </section>

      <section className="v5-manifesto">
        <div className="content-block glass-card">
          <h2>THE OMNI EXPERIENCE</h2>
          <p>
            Combining raw WebGL fluid dynamics, refractive glass architectures, 
            and kinetic layout physics. This is not just a layout; this is a living digital organism.
          </p>
        </div>
      </section>

      <section className="v5-projects">
        <h1 className="section-title">THE ARCHIVES</h1>
        <div className="project-list">
          <div className="project-item">
            <span className="p-num">01</span>
            <span className="p-name">Nexus Sync</span>
          </div>
          <div className="project-item">
            <span className="p-num">02</span>
            <span className="p-name">SquadSync Platform</span>
          </div>
          <div className="project-item">
            <span className="p-num">03</span>
            <span className="p-name">ZeroG Automator</span>
          </div>
        </div>
      </section>
      
      <footer className="v5-footer">
        <MagneticNode>
          <button className="giant-cta">INITIATE</button>
        </MagneticNode>
      </footer>
    </div>
  );
}
