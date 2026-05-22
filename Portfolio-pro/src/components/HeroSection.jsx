import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import './HeroSection.css';

export default function HeroSection() {
  const title1Ref = useRef(null);
  const title2Ref = useRef(null);
  const subtitleRef = useRef(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    const tl = gsap.timeline();

    tl.fromTo(title1Ref.current,
      { y: 100, opacity: 0 },
      { y: 0, opacity: 1, duration: 1, ease: 'power4.out', delay: 0.5 }
    )
    .fromTo(title2Ref.current,
      { y: 100, opacity: 0 },
      { y: 0, opacity: 1, duration: 1, ease: 'power4.out' },
      '-=0.8'
    )
    .fromTo(subtitleRef.current,
      { y: 30, opacity: 0 },
      { y: 0, opacity: 1, duration: 1, ease: 'power3.out' },
      '-=0.5'
    )
    .fromTo(scrollRef.current,
      { opacity: 0, y: -20 },
      { opacity: 1, y: 0, duration: 1, repeat: -1, yoyo: true, ease: 'power1.inOut' },
      '-=0.2'
    );
  }, []);

  return (
    <section className="hero-section">
      <div className="hero-content">
        <div className="hero-title-wrapper">
          <h1 ref={title1Ref} className="hero-title gradient-text glow">
            Crafting Digital
          </h1>
        </div>
        <div className="hero-title-wrapper">
          <h1 ref={title2Ref} className="hero-title outline-text">
            Experiences.
          </h1>
        </div>
        <p ref={subtitleRef} className="hero-subtitle glass-panel">
          Hi, I am a creative engineer specializing in modern web technologies, 
          AI integrations, and immersive user interfaces.
        </p>

        <div className="hero-cta-group">
          <a href="#projects" className="btn-primary interactable">View Work</a>
          <a href="#contact" className="btn-secondary interactable">Contact Me</a>
        </div>
      </div>
      
      <div ref={scrollRef} className="scroll-indicator">
        <span className="scroll-text">Scroll Down</span>
        <div className="scroll-arrow">↓</div>
      </div>
    </section>
  );
}
