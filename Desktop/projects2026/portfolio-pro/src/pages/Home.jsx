import { useState, useRef, useEffect } from 'react';
import CityBloxxGame from '../components/CityBloxxGame';
import '../components/V6Application.css';

// Typing effect component for the hero role
function TypingRole() {
  const roles = ['Cloud Engineer', 'DevOps Builder', 'AI Enthusiast', 'Python Developer'];
  const [ri, setRi] = useState(0);
  const [ci, setCi] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [text, setText] = useState('');

  useEffect(() => {
    let timer;
    const currentRole = roles[ri];
    
    if (!isDeleting) {
      timer = setTimeout(() => {
        setText(currentRole.slice(0, ci + 1));
        setCi(prev => prev + 1);
        if (ci + 1 === currentRole.length) {
          // Pause at the end of typing
          timer = setTimeout(() => {
            setIsDeleting(true);
          }, 1800);
        }
      }, 100);
    } else {
      timer = setTimeout(() => {
        setText(currentRole.slice(0, ci - 1));
        setCi(prev => prev - 1);
        if (ci - 1 === 0) {
          setIsDeleting(false);
          setRi(prev => (prev + 1) % roles.length);
        }
      }, 60);
    }

    return () => clearTimeout(timer);
  }, [ci, isDeleting, ri]);

  return (
    <div className="hero-role reveal reveal-delay-2">
      <span className="role-text">{text}</span>
      <span className="cursor-blink">|</span>
      <span className="role-static" style={{ color: 'var(--muted)' }}> / DevOps / AI Builder</span>
    </div>
  );
}

const PROJECTS = [
  {
    id: 'nexus-sync',
    status: 'LIVE',
    statusClass: 'status-live',
    dotClass: 'dot-live',
    icon: '⚡',
    name: 'NEXUS SYNC',
    desc: 'Fully automated data pipeline using Python & Selenium to scrape government portals, analyze with Pandas, and broadcast daily WhatsApp reports. Containerized with Docker, hosted 24/7 on AWS EC2 with GitHub Actions CI/CD.',
    chips: ['Python', 'Docker', 'AWS EC2', 'GitHub Actions', 'Selenium', 'Pandas'],
    upcoming: false
  },
  {
    id: 'node-deploy',
    status: 'LIVE',
    statusClass: 'status-live',
    dotClass: 'dot-live',
    icon: '🚀',
    name: 'NODE.JS CLOUD DEPLOY',
    desc: 'Production-ready Node.js application deployed on AWS EC2 with full IAM role configuration, security group setup, port management, and internet exposure — end-to-end hands-on cloud deployment.',
    chips: ['Node.js', 'AWS EC2', 'IAM'],
    upcoming: false
  },
  {
    id: 'ai-chatbot',
    status: 'IN DEVELOPMENT',
    statusClass: 'status-dev',
    dotClass: 'dot-dev',
    icon: '🤖',
    name: 'AI CHATBOT',
    desc: 'Context-aware Python chatbot powered by GPT API with memory, deployed as a cloud-hosted microservice with FastAPI and containerized via Docker.',
    chips: ['Python', 'GPT API', 'FastAPI', 'Docker'],
    upcoming: true
  },
  {
    id: 'cloud-cost',
    status: 'IN DEVELOPMENT',
    statusClass: 'status-dev',
    dotClass: 'dot-dev',
    icon: '📊',
    name: 'CLOUD COST DASHBOARD',
    desc: 'Real-time AWS cost visualization dashboard pulling CloudWatch metrics via Python — automated budget alerts, service breakdowns, and spend forecasting.',
    chips: ['AWS', 'CloudWatch', 'Python', 'Pandas'],
    upcoming: true
  },
  {
    id: 'devsecops',
    status: 'IN DEVELOPMENT',
    statusClass: 'status-dev',
    dotClass: 'dot-dev',
    icon: '🔐',
    name: 'DEVSECOPS PIPELINE',
    desc: 'Security-first CI/CD pipeline with Trivy vulnerability scanning integrated on every Docker build push — automated, zero-touch container security on GitHub Actions.',
    chips: ['Docker', 'Trivy', 'GitHub Actions', 'Terraform'],
    upcoming: true
  }
];

const CERTIFICATIONS = [
  {
    id: 'aws_training',
    icon: '☁️',
    name: 'AWS Web Services Training',
    by: 'Techwing',
    fileUrl: '/certificates/aws_training.png'
  },
  {
    id: 'chatgpt_intern',
    icon: '🤖',
    name: 'ChatGPT & Generative AI Internship',
    by: 'Blackbucks & IIDT',
    fileUrl: '/certificates/chatgpt_intern.png'
  },
  {
    id: 'cybersecurity_intern',
    icon: '🔐',
    name: 'AI & Cybersecurity Internship',
    by: 'AIMER Society',
    fileUrl: '/certificates/cybersecurity_intern.png'
  },
  {
    id: 'solutions_architecture',
    icon: '🏗️',
    name: 'Solutions Architecture Job Simulation',
    by: 'Forage',
    fileUrl: '/certificates/solutions_architecture.png'
  }
];

export default function Home() {
  const leftPaneRef = useRef(null);
  const [activeProjectModal, setActiveProjectModal] = useState(null);
  const [activeCertModal, setActiveCertModal] = useState(null);

  // Skill Card Glow movement
  const handleCardGlow = (e, cardEl) => {
    const r = cardEl.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width * 100).toFixed(1);
    const y = ((e.clientY - r.top) / r.height * 100).toFixed(1);
    cardEl.style.setProperty('--mx', `${x}%`);
    cardEl.style.setProperty('--my', `${y}%`);
  };

  useEffect(() => {
    const leftPane = leftPaneRef.current;
    if (!leftPane) return;

    // Pre-calculate section offsets to avoid layout thrashing in the scroll listener
    let sectionOffsets = [];
    const calculateOffsets = () => {
      const sections = leftPane.querySelectorAll('section[id]');
      sectionOffsets = Array.from(sections).map(s => ({
        id: s.id,
        top: s.offsetTop
      }));
    };

    calculateOffsets();

    // Watch for resizes to keep offsets accurate
    const resizeObserver = new ResizeObserver(() => {
      calculateOffsets();
    });
    resizeObserver.observe(leftPane);

    // Native IntersectionObserver for scroll reveals (run once per element)
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, {
      root: leftPane,
      rootMargin: '0px 0px -40px 0px',
      threshold: 0.05
    });

    const reveals = leftPane.querySelectorAll('.reveal');
    reveals.forEach(r => revealObserver.observe(r));

    // Highly optimized scroll listener
    const bar = document.getElementById('progress-bar');
    const navLinks = document.querySelectorAll('.nav-links a');
    let lastActiveId = 'hero';

    const handleScroll = () => {
      const scrollTop = leftPane.scrollTop;
      const scrollHeight = leftPane.scrollHeight;
      const clientHeight = leftPane.clientHeight;

      // Update progress bar
      const totalScrollable = scrollHeight - clientHeight;
      const scrollPct = totalScrollable > 0 ? (scrollTop / totalScrollable) * 100 : 0;
      if (bar) {
        bar.style.width = `${scrollPct}%`;
      }

      // Highlight active nav link based on pre-calculated section offsets
      const triggerPoint = scrollTop + clientHeight * 0.4;
      let activeId = 'hero';
      for (let i = 0; i < sectionOffsets.length; i++) {
        if (triggerPoint >= sectionOffsets[i].top) {
          activeId = sectionOffsets[i].id;
        }
      }

      if (activeId !== lastActiveId) {
        lastActiveId = activeId;
        navLinks.forEach(a => {
          if (a.getAttribute('href') === `#${activeId}`) {
            a.classList.add('active');
          } else {
            a.classList.remove('active');
          }
        });
      }
    };

    leftPane.addEventListener('scroll', handleScroll, { passive: true });
    
    // Allow layout to settle, then run scroll updates
    setTimeout(() => {
      calculateOffsets();
      handleScroll();
    }, 150);

    // Scroll to section requests (from navbar clicks)
    const handleScrollToSection = (e) => {
      const targetId = e.detail;
      const targetEl = leftPane.querySelector(`#${targetId}`);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    };
    window.addEventListener('scroll_to_section', handleScrollToSection);

    return () => {
      leftPane.removeEventListener('scroll', handleScroll);
      window.removeEventListener('scroll_to_section', handleScrollToSection);
      revealObserver.disconnect();
      resizeObserver.disconnect();
    };
  }, []);

  return (
    <main className="v6-main-layout" style={{ marginTop: '0px', padding: '0', height: '100vh', overflow: 'hidden' }}>
      {/* Scrollable Left Pane containing portfolio details */}
      <div className="left-pane" ref={leftPaneRef} style={{ height: '100%', overflowY: 'auto', paddingRight: '0' }}>
        
        {/* HERO SECTION */}
        <section id="hero" style={{ padding: '140px 6vw 80px' }}>
          <div className="hero-eyebrow reveal">Available for Opportunities</div>
          <h1 className="hero-name reveal reveal-delay-1">
            AKULA<br />ASHISH<br />KUMAR
            <div className="glitch-layer">AKULA<br />ASHISH<br />KUMAR</div>
          </h1>
          <TypingRole />
          <p className="hero-bio reveal reveal-delay-3">
            CS Graduate (2025) from Rajahmundry with real-world <em>AWS</em>, <em>Docker</em> &amp; <em>AI</em> experience.
            I build zero-touch automated pipelines, containerized cloud systems,
            and impactful software — driven by a passion for <em>continuous deployment</em>.
          </p>
          <div className="hero-cta reveal reveal-delay-4">
            <button 
              className="btn-primary" 
              onClick={() => window.dispatchEvent(new CustomEvent('scroll_to_section', { detail: 'projects' }))}
            >
              View Projects →
            </button>
            <button 
              className="btn-secondary"
              onClick={() => window.dispatchEvent(new CustomEvent('scroll_to_section', { detail: 'contact' }))}
            >
              Hire Me
            </button>
          </div>
          <div className="hero-stats reveal reveal-delay-5">
            <div className="stat"><span className="stat-num">3+</span><span className="stat-label">Internships</span></div>
            <div className="stat"><span className="stat-num">5+</span><span className="stat-label">Projects</span></div>
            <div className="stat"><span className="stat-num">4</span><span className="stat-label">Certifications</span></div>
            <div className="stat"><span className="stat-num">2025</span><span className="stat-label">Graduate</span></div>
          </div>
          <div className="scroll-indicator">
            <div className="scroll-line"></div>
            <span>SCROLL</span>
          </div>
        </section>

        {/* SKILLS SECTION */}
        <section id="skills" style={{ padding: '100px 6vw 80px' }}>
          <h2 className="sec-title reveal">Skills &amp; <span>Stack</span></h2>
          <p className="sec-sub reveal reveal-delay-1">Every tool I've mastered in the cloud, DevOps, and AI space.</p>
          
          <div className="skills-grid">
            <div 
              className="skill-card reveal reveal-delay-1"
              onMouseMove={(e) => handleCardGlow(e, e.currentTarget)}
            >
              <div className="skill-card-icon">☁️</div>
              <div className="skill-card-title">Cloud Technologies</div>
              <div className="skill-tags">
                <span className="stag c">AWS EC2</span>
                <span className="stag c">S3</span>
                <span className="stag c">IAM</span>
                <span className="stag c">VPC</span>
                <span className="stag c">CloudWatch</span>
                <span className="stag c">Lambda</span>
              </div>
            </div>

            <div 
              className="skill-card reveal reveal-delay-2"
              onMouseMove={(e) => handleCardGlow(e, e.currentTarget)}
            >
              <div className="skill-card-icon">⚙️</div>
              <div className="skill-card-title">DevOps &amp; Infra</div>
              <div className="skill-tags">
                <span className="stag g">Docker</span>
                <span className="stag g">Kubernetes</span>
                <span className="stag g">Terraform</span>
                <span className="stag g">GitHub Actions</span>
                <span className="stag g">CI/CD</span>
                <span className="stag g">Shell Script</span>
                <span className="stag g">Git</span>
              </div>
            </div>

            <div 
              className="skill-card reveal reveal-delay-3"
              onMouseMove={(e) => handleCardGlow(e, e.currentTarget)}
            >
              <div className="skill-card-icon">🐍</div>
              <div className="skill-card-title">Programming</div>
              <div className="skill-tags">
                <span className="stag p">Python</span>
                <span className="stag p">Linux</span>
                <span className="stag p">Selenium</span>
                <span className="stag p">Pandas</span>
                <span className="stag p">Bash</span>
              </div>
            </div>

            <div 
              className="skill-card reveal reveal-delay-4"
              onMouseMove={(e) => handleCardGlow(e, e.currentTarget)}
            >
              <div className="skill-card-icon">🤝</div>
              <div className="skill-card-title">Soft Skills</div>
              <div className="skill-tags">
                <span className="stag gold">Leadership</span>
                <span className="stag gold">Teamwork</span>
                <span className="stag gold">Problem-Solving</span>
                <span className="stag gold">Communication</span>
              </div>
            </div>
          </div>
        </section>

        {/* EXPERIENCE TIMELINE */}
        <section id="experience" style={{ padding: '100px 6vw 80px' }}>
          <h2 className="sec-title reveal">Work <span>Experience</span></h2>
          <p className="sec-sub reveal reveal-delay-1">Real-world internships that shaped my cloud and AI perspective.</p>
          
          <div className="timeline">
            <div className="tl-item reveal reveal-delay-1">
              <div className="tl-year">2024</div>
              <div className="tl-role">🤖 ChatGPT &amp; Generative AI Intern</div>
              <div className="tl-company">IIDT + Blackbucks</div>
              <div className="tl-desc">Explored enterprise applications of conversational AI — ChatGPT and Gemini — building real use-case demos and understanding prompt engineering at scale.</div>
            </div>
            
            <div className="tl-item reveal reveal-delay-2">
              <div className="tl-year">2023</div>
              <div className="tl-role">☁️ AWS Cloud Intern</div>
              <div className="tl-company">Techwing</div>
              <div className="tl-desc">Hands-on deployment of EC2 instances, S3 buckets, and IAM policies. Designed and executed real-world cloud architecture scenarios from scratch.</div>
            </div>
            
            <div className="tl-item reveal reveal-delay-3">
              <div className="tl-year">2023</div>
              <div className="tl-role">🔐 AI Intern (Short-Term)</div>
              <div className="tl-company">AIMER Society</div>
              <div className="tl-desc">Studied AI tools and cybersecurity fundamentals. Completed small-scale AI application projects demonstrating real-world vulnerability awareness.</div>
            </div>
          </div>
        </section>

        {/* PROJECTS SECTION */}
        <section id="projects" style={{ padding: '100px 6vw 80px' }}>
          <h2 className="sec-title reveal">My <span>Projects</span></h2>
          <p className="sec-sub reveal reveal-delay-1">Shipped and upcoming projects — from cloud automation to AI systems.</p>
          
          <div className="projects-grid">
            {PROJECTS.map((proj, idx) => {
              const delayClass = `reveal-delay-${(idx % 3) + 1}`;
              return (
                <div 
                  key={proj.id}
                  className={`proj-card ${proj.upcoming ? 'upcoming' : ''} reveal ${delayClass}`}
                  onClick={() => setActiveProjectModal(proj)}
                >
                  <div className="proj-header">
                    <div className={`proj-status ${proj.statusClass}`}>
                      <span className={`status-dot ${proj.dotClass}`}></span>{proj.status}
                    </div>
                    <div className="proj-expand-icon">
                      <svg 
                        className="chevron-icon" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor" 
                        strokeWidth="2.5" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"
                        style={{ transform: 'none' }}
                      >
                        <path d="M15 3h6v6"></path>
                        <path d="M10 14L21 3"></path>
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                      </svg>
                    </div>
                  </div>
                  
                  <div className="proj-icon">{proj.icon}</div>
                  <div className="proj-name">{proj.name}</div>

                  <div className="proj-chips" style={{ marginTop: '16px' }}>
                    {proj.chips.map((chip, cIdx) => (
                      <span 
                        key={cIdx} 
                        className={`chip ${proj.upcoming ? 'green' : ''}`}
                        style={{ fontSize: '12px', padding: '5px 12px', fontWeight: '600' }}
                      >
                        {chip}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* EDUCATION */}
        <section id="education" style={{ padding: '60px 6vw 40px' }}>
          <h2 className="sec-title reveal"><span>Education</span></h2>
          <p className="sec-sub reveal reveal-delay-1">Academic foundations that built my technical depth.</p>
          
          <div className="edu-grid">
            <div className="edu-card reveal reveal-delay-1">
              <div className="edu-year-badge">2021 — 2025</div>
              <div className="edu-degree">B.Tech — Computer Science Engineering</div>
              <div className="edu-inst">Godavari Institute of Engineering &amp; Technology (Autonomous), JNTUK</div>
            </div>
            
            <div className="edu-card reveal reveal-delay-2">
              <div className="edu-year-badge">2019 — 2022</div>
              <div className="edu-degree">Diploma in Engineering</div>
              <div className="edu-inst">Adithya Polytechnic College, SBTET</div>
            </div>
            
            <div className="edu-card reveal reveal-delay-3">
              <div className="edu-year-badge">Completed 2019</div>
              <div className="edu-degree">Secondary School Certificate</div>
              <div className="edu-inst">Oxford Concept School, BSEAP</div>
            </div>
          </div>
        </section>

        {/* HOBBIES */}
        <section id="hobbies" style={{ padding: '40px 6vw 40px' }}>
          <span className="sec-label reveal">Beyond the Screen</span>
          <h2 className="sec-title reveal reveal-delay-1">What <span>Drives</span> Me</h2>
          <p className="sec-sub reveal reveal-delay-2">Outside of work, these are the things that keep me energized, curious, and constantly growing.</p>

          <div className="hobbies-grid">
            {[
              { icon: '🎮', word: 'GAMING', tagline: 'Strategy & Reflexes', desc: 'Games sharpen my problem-solving, patience, and competitive edge. Every match is a system to master.', accent: 'c', delay: 1, anim: 'gaming' },
              { icon: '✨', word: 'VIBE CODING', tagline: 'Flow State Building', desc: 'Putting on lo-fi, opening VS Code, and letting ideas flow. Some of my best projects were born at 2am.', accent: 'p', delay: 2, anim: 'coding' },
              { icon: '🎵', word: 'MUSIC', tagline: 'Sound & Focus', desc: 'Music is my background engine — the right playlist unlocks focus mode and fuels long coding sessions.', accent: 'g', delay: 3, anim: 'music' },
              { icon: '🔧', word: 'BUILDING', tagline: 'Always Shipping', desc: "I'm never not building something. From small scripts to full systems — if there's a problem, I'm automating it.", accent: 'c', delay: 4, anim: 'building' },
              { icon: '📡', word: 'TECH RADAR', tagline: 'Always Up-To-Date', desc: 'I wake up and check what dropped overnight. AI releases, cloud announcements, new frameworks — I live for this.', accent: 'gold', delay: 1, anim: 'radar' }
            ].map((h, i) => (
              <div key={i} className={`hobby-card reveal reveal-delay-${h.delay}`}>
                <div className="hobby-card-top">
                  <div className={`hobby-icon-wrap hobby-accent-${h.accent}`}>
                    <span className="hobby-icon">{h.icon}</span>
                  </div>
                  {/* Mini in-card animation */}
                  <div className={`hobby-anim anim-${h.anim}`}>
                    {h.anim === 'gaming' && (<>
                      <div className="game-ground" />
                      <div className="game-dot gd1" /><div className="game-dot gd2" /><div className="game-dot gd3" />
                    </>)}
                    {h.anim === 'coding' && (
                      <div className="code-scroll">
                        {[{w:'70%',c:'c'},{w:'50%',c:'p'},{w:'85%',c:'w'},{w:'60%',c:'c'},{w:'75%',c:'g'},{w:'45%',c:'p'},{w:'70%',c:'c'},{w:'50%',c:'p'},{w:'85%',c:'w'},{w:'60%',c:'c'},{w:'75%',c:'g'},{w:'45%',c:'p'}].map((l,li)=>(
                          <div key={li} className={`code-ln cl-${l.c}`} style={{width:l.w}} />
                        ))}
                      </div>
                    )}
                    {h.anim === 'music' && (<>
                      {[1,2,3,4,5,6,7].map(n=><div key={n} className={`eq-bar eb${n}`}/>)}
                    </>)}
                    {h.anim === 'building' && (<>
                      <div className="h-gear" />
                      <div className="build-col">
                        <div className="bb bb3" /><div className="bb bb2" /><div className="bb bb1" />
                      </div>
                    </>)}
                    {h.anim === 'radar' && (<>
                      <div className="rr rr3"/><div className="rr rr2"/><div className="rr rr1"/>
                      <div className="radar-sweep"/>
                      <div className="rblip rb1"/><div className="rblip rb2"/>
                    </>)}
                  </div>
                </div>
                <div className="hobby-word">{h.word}</div>
                <div className="hobby-tagline">{h.tagline}</div>
                <p className="hobby-desc">{h.desc}</p>
              </div>
            ))}

          </div>
        </section>

        {/* CERTIFICATIONS */}
        <section id="certs" style={{ padding: '40px 6vw 40px' }}>
          <h2 className="sec-title reveal"><span>Certifications</span></h2>
          <p className="sec-sub reveal reveal-delay-1">Industry-recognized credentials validating my expertise.</p>
          
          <div className="certs-grid">
            {CERTIFICATIONS.map((cert, idx) => {
              const delayClass = `reveal-delay-${(idx % 4) + 1}`;
              return (
                <div 
                  key={cert.id} 
                  className={`cert-card reveal ${delayClass}`}
                  onClick={() => setActiveCertModal(cert)}
                >
                  <div className="cert-ico">{cert.icon}</div>
                  <div>
                    <div className="cert-name">{cert.name}</div>
                    <div className="cert-by">{cert.by}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* CONTACT */}
        <section id="contact" style={{ padding: '40px 6vw 100px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div className="contact-card reveal">
            <h2 className="sec-title" style={{ textAlign: 'center', marginTop: '10px' }}>Let's <span>Build</span> Together</h2>
            <p style={{ color: 'var(--muted)', fontSize: '15px', lineHeight: '1.7', maxWidth: '420px', textAlign: 'center', margin: '0 auto' }}>
              Open to entry-level Cloud, DevOps &amp; AI roles. I bring energy, curiosity, and a passion for shipping things that work.
            </p>
            
            <div className="contact-links">
              <a className="contact-link" href="tel:9951092727">
                <em>📞</em><span className="cl-label">Phone</span><span className="cl-val">99510 92727</span>
              </a>
              <a className="contact-link" href="mailto:akulaashish27@gmail.com">
                <em>✉️</em><span className="cl-label">Email</span><span className="cl-val">akulaashish27@gmail.com</span>
              </a>
              <a className="contact-link" href="https://linkedin.com/in/akula-ashish-kumar" target="_blank" rel="noreferrer">
                <em>💼</em><span className="cl-label">LinkedIn</span><span className="cl-val">akula-ashish-kumar</span>
              </a>
              <a className="contact-link" href="https://github.com/ashish27272git" target="_blank" rel="noreferrer">
                <em>🐙</em><span className="cl-label">GitHub</span><span className="cl-val">ashish27272git</span>
              </a>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '24px' }}>
              <a 
                href="/resume.pdf" 
                download="Akula_Ashish_Kumar_Resume.pdf"
                className="hire-btn"
                style={{ textDecoration: 'none' }}
              >
                HIRE ME →
              </a>
            </div>
          </div>

          <footer style={{ marginTop: '80px', width: '100%', borderTop: '1px solid var(--border)', paddingTop: '20px', textAlign: 'center' }}>
            <p style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: '10px', color: 'var(--muted)', letterSpacing: '2px' }}>
              © 2025 AKULA ASHISH KUMAR &nbsp;·&nbsp; BUILT WITH PASSION &nbsp;·&nbsp; RAJAHMUNDRY, INDIA
            </p>
          </footer>
        </section>
      </div>

      {/* Transparent City Bloxx Stacker on the right side */}
      <div className="right-pane" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
        <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', width: '100%', height: '100%' }}>
          <CityBloxxGame />
        </div>
      </div>
      {/* Project Modal Overlay */}
      {activeProjectModal && (
        <div className="modal-overlay" onClick={() => setActiveProjectModal(null)}>
          <div className="modal-content project-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setActiveProjectModal(null)}>✕</button>
            <div className="modal-header">
              <div className={`proj-status ${activeProjectModal.statusClass}`} style={{ display: 'inline-flex', marginBottom: '12px' }}>
                <span className={`status-dot ${activeProjectModal.dotClass}`}></span>{activeProjectModal.status}
              </div>
            </div>
            <div className="modal-body">
              <div className="modal-project-icon">{activeProjectModal.icon}</div>
              <h3 className="modal-project-title">{activeProjectModal.name}</h3>
              <p className="modal-project-desc">{activeProjectModal.desc}</p>
              
              <h4 className="modal-section-title">Tools &amp; Tech</h4>
              <div className="modal-project-chips">
                {activeProjectModal.chips.map((chip, cIdx) => (
                  <span key={cIdx} className={`chip ${activeProjectModal.upcoming ? 'green' : ''}`} style={{ fontSize: '11px', padding: '4px 10px' }}>
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Certificate Modal Overlay */}
      {activeCertModal && (
        <div className="modal-overlay" onClick={() => setActiveCertModal(null)}>
          <div className="modal-content cert-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setActiveCertModal(null)}>✕</button>
            <div className="modal-header-bar">
              <div className="modal-title-info">
                <span className="modal-cert-ico">{activeCertModal.icon}</span>
                <div>
                  <h3 className="modal-cert-title">{activeCertModal.name}</h3>
                  <p className="modal-cert-issuer">Issued by {activeCertModal.by}</p>
                </div>
              </div>
            </div>
            
            <div className="modal-preview-body">
              {activeCertModal.fileUrl.toLowerCase().endsWith('.pdf') ? (
                <iframe 
                  src={activeCertModal.fileUrl} 
                  className="cert-iframe-preview" 
                  title={activeCertModal.name}
                />
              ) : (
                <div className="cert-image-preview-container">
                  <img 
                    src={activeCertModal.fileUrl} 
                    className="cert-image-preview" 
                    alt={activeCertModal.name} 
                  />
                </div>
              )}
            </div>

            <div className="modal-footer-links">
              Want to download? <a href={activeCertModal.fileUrl} download target="_blank" rel="noreferrer">Open raw file</a>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
