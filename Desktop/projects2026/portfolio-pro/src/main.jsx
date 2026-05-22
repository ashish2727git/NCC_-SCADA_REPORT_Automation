import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Global polyfill for CanvasRenderingContext2D.roundRect for maximum browser compatibility
if (typeof window !== 'undefined' && window.CanvasRenderingContext2D && !window.CanvasRenderingContext2D.prototype.roundRect) {
  window.CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
    const maxRadius = Math.min(Math.abs(w) / 2, Math.abs(h) / 2);
    let radius = r;
    if (typeof r === 'object') {
      radius = Math.min(maxRadius, r[0] || r.tl || 0);
    } else {
      radius = Math.min(maxRadius, Number(r) || 0);
    }
    this.beginPath();
    this.moveTo(x + radius, y);
    this.arcTo(x + w, y, x + w, y + h, radius);
    this.arcTo(x + w, y + h, x, y + h, radius);
    this.arcTo(x, y + h, x, y, radius);
    this.arcTo(x, y, x + w, y, radius);
    this.closePath();
    return this;
  };
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

