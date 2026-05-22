import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import InteractiveBackground from './components/InteractiveBackground';
import Navbar from './components/Navbar';

import Home from './pages/Home';
import Projects from './pages/Projects';
import About from './pages/About';
import Contact from './pages/Contact';

// Visual Experiences
import ManuscriptExperience from './components/Manuscript/ManuscriptExperience';

export default function App() {
  return (
    <Router basename={import.meta.env.BASE_URL.replace(/\/$/, '')}>
      <div style={{ backgroundColor: 'var(--bg)', minHeight: '100vh', position: 'relative', overflow: 'hidden', transition: 'background-color 0.5s ease, color 0.5s ease' }}>
        <InteractiveBackground />
        <Navbar />
        
        <div style={{ position: 'relative', zIndex: 10 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/v7" element={<ManuscriptExperience />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

