import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import './ProjectsSection.css';

gsap.registerPlugin(ScrollTrigger);

const PROJECTS = [
  {
    id: 1,
    title: 'Nexus Sync Pro',
    category: 'Desktop App',
    description: 'High-performance Python desktop environment with auto-provisioning and shortcut management.',
    image: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=1000'
  },
  {
    id: 2,
    title: 'SquadSync Platform',
    category: 'Esports Comms',
    description: 'Real-time competitive communication tool featuring 3D integrations and enterprise architecture.',
    image: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&q=80&w=1000'
  },
  {
    id: 3,
    title: 'ZeroG Automator',
    category: 'Chrome Extension',
    description: 'Vision-based AI automation tool injecting real-time passenger data into flight booking portals.',
    image: 'https://images.unsplash.com/photo-1614729939124-032f0b5619ce?auto=format&fit=crop&q=80&w=1000'
  }
];

export default function ProjectsSection() {
  const containerRef = useRef(null);
  const cardsRef = useRef([]);

  useEffect(() => {
    // Stagger card entrance
    cardsRef.current.forEach((card, i) => {
      gsap.fromTo(card,
        { y: 100, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: card,
            start: 'top 85%',
            end: 'top 50%',
            toggleActions: 'play none none reverse'
          }
        }
      );
    });
  }, []);

  const handleMouseMove = (e, index) => {
    const card = cardsRef.current[index];
    if (!card) return;

    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    const rotateX = ((y - centerY) / centerY) * -10;
    const rotateY = ((x - centerX) / centerX) * 10;

    gsap.to(card, {
      rotateX,
      rotateY,
      duration: 0.5,
      ease: 'power2.out',
      transformPerspective: 1000,
    });
  };

  const handleMouseLeave = (index) => {
    const card = cardsRef.current[index];
    if (card) {
      gsap.to(card, {
        rotateX: 0,
        rotateY: 0,
        duration: 0.5,
        ease: 'power2.out'
      });
    }
  };

  return (
    <section id="projects" className="projects-section" ref={containerRef}>
      <div className="container">
        <h2 className="section-title">Featured Work</h2>
        
        <div className="projects-grid">
          {PROJECTS.map((project, index) => (
            <div
              key={project.id}
              ref={el => cardsRef.current[index] = el}
              className="project-card interactable"
              onMouseMove={(e) => handleMouseMove(e, index)}
              onMouseLeave={() => handleMouseLeave(index)}
            >
              <div className="project-image">
                <img src={project.image} alt={project.title} loading="lazy" />
                <div className="project-overlay">
                  <span>View Details</span>
                </div>
              </div>
              <div className="project-info">
                <span className="project-category">{project.category}</span>
                <h3 className="project-title">{project.title}</h3>
                <p className="project-desc">{project.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
