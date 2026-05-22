import { useEffect, useRef } from 'react';
import './SkillsSnowfall.css';

const SKILLS = [
  'React', 'Python', 'JavaScript', 'TypeScript', 'Node.js', 
  'Three.js', 'WebGL', 'GSAP', 'OpenCV', 'WebRTC', 
  'Selenium', 'Git', 'CSS3', 'HTML5', 'SQL', 'SCADA', 
  'Canvas', 'Vite', 'PyInstaller', 'Chrome Extension'
];

export default function SkillsSnowfall() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: -1000, y: -1000, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let particles = [];
    
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initialize particles
    const initParticles = () => {
      particles = [];
      const particleCount = Math.min(60, Math.floor((window.innerWidth * window.innerHeight) / 25000));
      
      for (let i = 0; i < particleCount; i++) {
        particles.push(createParticle(true));
      }
    };

    const createParticle = (randomY = false) => {
      const skill = SKILLS[Math.floor(Math.random() * SKILLS.length)];
      const size = Math.random() * 8 + 12; // Font size 12px to 20px
      return {
        x: Math.random() * canvas.width,
        y: randomY ? Math.random() * canvas.height : -30,
        vx: (Math.random() - 0.5) * 0.5,
        vy: Math.random() * 0.8 + 0.4, // Falling speed
        size: size,
        text: skill,
        alpha: Math.random() * 0.4 + 0.15, // opacity
        angle: Math.random() * Math.PI * 2,
        spin: (Math.random() - 0.5) * 0.01,
        // For physics repulsion
        targetVx: 0,
        targetVy: 0,
        pushX: 0,
        pushY: 0
      };
    };

    initParticles();

    // Mouse events
    const handleMouseMove = (e) => {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
      mouseRef.current.active = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.active = false;
      mouseRef.current.x = -1000;
      mouseRef.current.y = -1000;
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);

    // Game loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const mouse = mouseRef.current;
      const repelRadius = 150;
      const repelForce = 3;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        
        // Horizontal swaying
        p.angle += p.spin;
        const drift = Math.sin(p.angle) * 0.25;

        // Apply mouse repulsion if active
        if (mouse.active) {
          const dx = p.x - mouse.x;
          const dy = p.y - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < repelRadius) {
            // Stronger push the closer the mouse is
            const force = (repelRadius - dist) / repelRadius;
            const angle = Math.atan2(dy, dx);
            
            p.pushX += Math.cos(angle) * force * repelForce;
            p.pushY += Math.sin(angle) * force * repelForce;
          }
        }

        // Apply velocities and drag
        p.pushX *= 0.92; // decay push
        p.pushY *= 0.92;

        p.x += p.vx + drift + p.pushX;
        p.y += p.vy + p.pushY;

        // Wrap around boundaries
        if (p.x < -100) p.x = canvas.width + 50;
        if (p.x > canvas.width + 100) p.x = -50;
        
        // Reset if falls past screen bottom
        if (p.y > canvas.height + 40) {
          particles[i] = createParticle(false);
          continue;
        }

        // Draw particle
        ctx.save();
        ctx.font = `600 ${p.size}px 'Space Grotesk', 'Outfit', sans-serif`;
        ctx.shadowBlur = 10;
        
        // Subtle alternate glowing colors (Neon Cyan / Neon Pink / Purple)
        if (i % 3 === 0) {
          ctx.fillStyle = `rgba(0, 240, 255, ${p.alpha})`; // neon cyan
          ctx.shadowColor = `rgba(0, 240, 255, ${p.alpha * 0.5})`;
        } else if (i % 3 === 1) {
          ctx.fillStyle = `rgba(255, 0, 128, ${p.alpha})`; // neon pink
          ctx.shadowColor = `rgba(255, 0, 128, ${p.alpha * 0.5})`;
        } else {
          ctx.fillStyle = `rgba(180, 80, 255, ${p.alpha})`; // neon purple
          ctx.shadowColor = `rgba(180, 80, 255, ${p.alpha * 0.5})`;
        }

        ctx.translate(p.x, p.y);
        ctx.rotate(p.angle * 0.05); // subtle text tilt
        ctx.fillText(p.text, 0, 0);
        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} className="skills-snowfall-canvas" />;
}
