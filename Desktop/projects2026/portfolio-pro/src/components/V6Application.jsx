import { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Cpu, CheckCircle2 } from 'lucide-react';
import './V6Application.css';

const MOCK_INTENTS = {
  'projects': "I've built several critical systems. 'Nexus Sync Pro' is a Python desktop orchestrator. 'SquadSync' is a competitive esports comms platform. 'ZeroG Automator' is a computer-vision based Chrome extension for real-time flight data injection.",
  'skills': "My core stack focuses on extreme capability: React 19, Three.js/WebGL for massive graphical processing, Python for deep system automation, and raw GSAP/physics for kinetic UI design.",
  'contact': "You can initialize contact via email at root@studio.ai or ping the neural network directly on LinkedIn.",
  'default': "I am the Portfolio AI. Try asking me about 'projects', 'skills', or 'contact'."
};

function AIChatbot() {
  const [messages, setMessages] = useState([{ sender: 'ai', text: MOCK_INTENTS['default'] }]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef(null);

  const scrollToBottom = () => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setInput('');
    setIsTyping(true);

    // Simulate AI thinking and response
    setTimeout(() => {
      const lower = userMsg.toLowerCase();
      let response = MOCK_INTENTS['default'];
      
      if (lower.includes('project') || lower.includes('work') || lower.includes('build')) {
        response = MOCK_INTENTS['projects'];
      } else if (lower.includes('skill') || lower.includes('stack') || lower.includes('tech')) {
        response = MOCK_INTENTS['skills'];
      } else if (lower.includes('contact') || lower.includes('email') || lower.includes('hire')) {
        response = MOCK_INTENTS['contact'];
      }

      setMessages(prev => [...prev, { sender: 'ai', text: response }]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000); // Random delay 1s - 2s
  };

  return (
    <div className="ai-chatbot-container glass-panel">
      <div className="chat-header">
        <Cpu size={20} className="text-cyan" />
        <span className="font-display">PORTFOLIO ASSISTANT v1.0</span>
        <span className="status-dot"></span>
      </div>
      
      <div className="chat-history">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.sender}`}>
            {msg.sender === 'ai' && <Terminal size={14} className="msg-icon" />}
            <p>{msg.text}</p>
          </div>
        ))}
        {isTyping && (
          <div className="chat-message ai typing">
            <span className="dot"></span><span className="dot"></span><span className="dot"></span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="chat-input-area" onSubmit={handleSubmit}>
        <input 
          type="text" 
          placeholder="Ask me anything..." 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="chat-input"
        />
        <button type="submit" className="chat-submit" disabled={!input.trim() || isTyping}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}

function ProjectCard({ title, desc, tech }) {
  return (
    <div className="project-card-v6 glass-panel">
      <h3 className="font-display">{title}</h3>
      <p>{desc}</p>
      <div className="tech-stack">
        {tech.map((t, i) => (
          <span key={i} className="tech-badge"><CheckCircle2 size={12}/> {t}</span>
        ))}
      </div>
    </div>
  );
}

export default function V6Application() {
  return (
    <div className="v6-app-wrapper">
      <header className="v6-header">
        <div className="logo font-display">SYSTEM.INIT()</div>
      </header>

      <main className="v6-main-layout">
        <div className="left-pane">
          <div className="intro-block">
            <h1 className="font-display massive-headline">INTELLIGENT<br/>DESIGN.</h1>
            <p className="subtitle">
              Visuals are irrelevant without function. Welcome to a portfolio designed as a living application. Ask the AI about my history, or explore the active systems below.
            </p>
          </div>
          
          <div className="projects-grid-v6">
            <ProjectCard 
              title="Nexus Sync Pro" 
              desc="A Python desktop orchestrator manipulating raw system environments."
              tech={['Python', 'PyInstaller', 'OS APIs']}
            />
            <ProjectCard 
              title="SquadSync" 
              desc="Competitive esports communication network built on WebRTC and React."
              tech={['React', 'Supabase', 'WebRTC']}
            />
            <ProjectCard 
              title="ZeroG Automator" 
              desc="Vision-based AI logic interacting natively with browser DOM."
              tech={['JavaScript', 'Chrome APIs', 'Computer Vision']}
            />
          </div>
        </div>

        <div className="right-pane">
          <AIChatbot />
        </div>
      </main>
    </div>
  );
}
