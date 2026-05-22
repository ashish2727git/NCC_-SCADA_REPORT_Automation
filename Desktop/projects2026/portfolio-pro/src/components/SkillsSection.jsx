import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import './SkillsSection.css';

gsap.registerPlugin(ScrollTrigger);

const SKILLS = [
  'React', 'Three.js', 'WebGL', 'GSAP', 'Framer Motion', 
  'Node.js', 'Python', 'AI Integration', 'Tailwind CSS', 'Vite',
  'Next.js', 'TypeScript', 'Responsive Design', 'UX/UI'
];

export default function SkillsSection() {
  const scrollRef = useRef(null);

  useEffect(() => {
    // Horizontal scroll effect
    const container = scrollRef.current;
    
    gsap.to(container, {
      xPercent: -50,
      ease: "none",
      scrollTrigger: {
        trigger: ".skills-section",
        start: "top bottom",
        end: "bottom top",
        scrub: 1,
      }
    });

  }, []);

  return (
    <section className="skills-section">
      <div className="skills-ticker">
        <div className="skills-track" ref={scrollRef}>
          {/* Double the skills for infinite effect visually with scroll */}
          {[...SKILLS, ...SKILLS, ...SKILLS].map((skill, index) => (
            <div key={index} className="skill-item">
              <span className="skill-dot"></span>
              {skill}
            </div>
          ))}
        </div>
      </div>
      <div className="skills-description container">
        <h2>Tech Arsenal</h2>
        <p>Combining the power of modern web frameworks, 3D graphics, and AI integrations to build experiences that push the boundaries of what is possible in the browser.</p>
      </div>
    </section>
  );
}
