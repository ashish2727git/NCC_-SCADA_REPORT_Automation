import { useEffect, useRef, useState } from 'react';
import './HTMLOverlay.css';

// Glitch decode effect function
const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
function runGlitchDecrypt(targetText, setFn, speed = 30) {
  let iteration = 0;
  const maxIterations = targetText.length;
  
  const interval = setInterval(() => {
    const current = targetText
      .split('')
      .map((char, index) => {
        if (char === ' ') return ' ';
        if (index < iteration) {
          return targetText[index];
        }
        return chars[Math.floor(Math.random() * chars.length)];
      })
      .join('');
      
    setFn(current);
    
    if (iteration >= maxIterations) {
      clearInterval(interval);
    }
    
    iteration += 1 / 3; 
  }, speed);
  
  return interval;
}

export default function HTMLOverlay() {
  const [heroText, setHeroText] = useState('');
  const [subText, setSubText] = useState('');
  
  const heroTarget = "SYSTEM.INITIALIZED //";
  const subTarget = "God-Tier WebGL Experience Active.";

  useEffect(() => {
    // Sequence the decrypt effect
    const subInterval = runGlitchDecrypt(subTarget, setSubText, 20);
    setTimeout(() => {
      runGlitchDecrypt(heroTarget, setHeroText, 40);
    }, 500);

    return () => clearInterval(subInterval);
  }, []);

  return (
    <div className="html-overlay-container">
      <div className="overlay-content hero-section-v2">
        <h1 className="glitch-text">{heroText}</h1>
        <p className="cyber-subtitle">{subText}</p>
        <div className="scroll-hint">[ SCROLL TO INITIATE FLIGHT ]</div>
      </div>
    </div>
  );
}
