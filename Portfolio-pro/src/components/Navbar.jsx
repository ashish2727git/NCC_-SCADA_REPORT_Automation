import { useEffect, useState, useRef } from 'react';
import MagneticNode from './MagneticNode';
import './Navbar.css';

const THEMES = [
  { id: 'dark-scifi', name: 'Dark Sci-Fi', colors: ['#00f5ff', '#b44fff', '#020609'] },
  { id: 'glossy-light', name: 'Glossy Light', colors: ['#0066cc', '#8b00ff', '#f4f7f9'] },
  { id: 'pleasant-coloured', name: 'Pleasant Coloured', colors: ['#e07a5f', '#f2cc8f', '#faf7f2'] },
  { id: 'cyberpunk-neon', name: 'Cyberpunk Neon', colors: ['#f3f315', '#ff0055', '#05000a'] },
  { id: 'forest-moss', name: 'Forest Moss', colors: ['#2ec4b6', '#20bf55', '#09120c'] },
  { id: 'sunset-amber', name: 'Sunset Amber', colors: ['#f07167', '#ffb703', '#140b10'] },
  { id: 'synthwave-80s', name: 'Synthwave 80s', colors: ['#ff007f', '#390099', '#0e051c'] },
  { id: 'dracula-vamp', name: 'Dracula Vamp', colors: ['#ff5555', '#bd93f9', '#1a1a24'] },
  { id: 'oceanic-abyss', name: 'Oceanic Abyss', colors: ['#00b4d8', '#0077b6', '#010c1e'] },
  { id: 'monochrome-stark', name: 'Monochrome Stark', colors: ['#ffffff', '#aaaaaa', '#000000'] }
];

export default function Navbar() {
  const [selectedTheme, setSelectedTheme] = useState('dark-scifi');
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem('portfolio-theme') || 'dark-scifi';
    setSelectedTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Slight delay to allow DOM to paint and trigger canvas updates
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('theme-changed', { detail: savedTheme }));
    }, 100);

    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleThemeChange = (themeId) => {
    setSelectedTheme(themeId);
    document.documentElement.setAttribute('data-theme', themeId);
    localStorage.setItem('portfolio-theme', themeId);
    window.dispatchEvent(new CustomEvent('theme-changed', { detail: themeId }));
    setIsOpen(false);
  };

  const handleNavClick = (e, targetId) => {
    e.preventDefault();
    window.dispatchEvent(new CustomEvent('scroll_to_section', { detail: targetId }));
    
    // Explicitly toggle active class in Navbar immediately
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(a => {
      a.classList.remove('active');
      if (a.getAttribute('href') === `#${targetId}`) {
        a.classList.add('active');
      }
    });
  };

  return (
    <header className="v6-header global-nav">
      <div className="nav-logo font-display">PORTFOLIO</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <nav className="nav-links">
          <MagneticNode>
            <a href="#hero" className="active" onClick={(e) => handleNavClick(e, 'hero')}>Home</a>
          </MagneticNode>
          <MagneticNode>
            <a href="#skills" onClick={(e) => handleNavClick(e, 'skills')}>Skills</a>
          </MagneticNode>
          <MagneticNode>
            <a href="#experience" onClick={(e) => handleNavClick(e, 'experience')}>Experience</a>
          </MagneticNode>
          <MagneticNode>
            <a href="#projects" onClick={(e) => handleNavClick(e, 'projects')}>Projects</a>
          </MagneticNode>
          <MagneticNode>
            <a href="#contact" onClick={(e) => handleNavClick(e, 'contact')}>Contact</a>
          </MagneticNode>
        </nav>

        {/* Custom Theme Dropdown Widget */}
        <div className="theme-selector-container" ref={dropdownRef}>
          <button className="theme-selector-trigger" onClick={() => setIsOpen(!isOpen)}>
            <span>Theme: {THEMES.find(t => t.id === selectedTheme)?.name || 'Dark Sci-Fi'}</span>
            <span className="theme-indicator-dots">
              {THEMES.find(t => t.id === selectedTheme)?.colors.map((c, i) => (
                <span key={i} className="theme-dot" style={{ backgroundColor: c }}></span>
              ))}
            </span>
          </button>
          {isOpen && (
            <div className="theme-dropdown-list">
              {THEMES.map((theme) => (
                <button
                  key={theme.id}
                  className={`theme-dropdown-item ${selectedTheme === theme.id ? 'active' : ''}`}
                  onClick={() => handleThemeChange(theme.id)}
                >
                  <span>{theme.name}</span>
                  <span className="theme-indicator-dots">
                    {theme.colors.map((c, i) => (
                      <span key={i} className="theme-dot" style={{ backgroundColor: c }}></span>
                    ))}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      {/* Scroll Progress Bar at the top of the header */}
      <div id="progress-bar" style={{ width: '0%' }}></div>
    </header>
  );
}
