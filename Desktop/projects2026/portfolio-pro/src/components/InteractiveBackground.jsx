import { useEffect, useRef } from 'react';
import './InteractiveBackground.css';

const SKILL_ITEMS = [
  { text: 'AWS', label: 'AWS Cloud Services', color: '#ffd060' },
  { text: 'Docker', label: 'Docker Containerization', color: '#00f5ff' },
  { text: 'Kubernetes', label: 'Kubernetes Orchestration', color: '#00e896' },
  { text: 'Terraform', label: 'Terraform IaC', color: '#b44fff' },
  { text: 'Python', label: 'Python Systems & Scripting', color: '#ffd060' },
  { text: 'Node.js', label: 'Node.js Backend Services', color: '#00e896' },
  { text: 'Git', label: 'Git & Version Control', color: '#b44fff' },
  { text: 'Linux', label: 'Linux OS Administration', color: '#ffd060' },
  { text: 'AI', label: 'GenAI & Neural Networks', color: '#b44fff' },
  { text: 'CI/CD', label: 'CI/CD Automated Pipelines', color: '#00f5ff' },
  { text: 'Bash', label: 'Shell & Bash Scripting', color: '#00e896' },
  { text: 'Selenium', label: 'Web Scrapers & Automation', color: '#ff3b30' }
];

// Helper to draw clean textless vector tool icons on canvas
const drawToolIcon = (ctx, x, y, w, h, tool, colors = { c: '#00f5ff', p: '#b44fff', g: '#00e896', gold: '#ffd060', bg: '#020609' }) => {
  ctx.save();
  ctx.translate(x, y);

  const baseSize = 40;
  const scale = w / baseSize;
  ctx.scale(scale, scale);

  const cx = baseSize / 2;
  const cy = baseSize / 2;

  ctx.lineWidth = 2.0;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  switch (tool) {
    case 'AWS':
      // Amazon cloud outline
      ctx.strokeStyle = colors.gold;
      ctx.beginPath();
      ctx.arc(cx - 7, cy + 1, 5, Math.PI * 0.8, Math.PI * 1.8);
      ctx.arc(cx, cy - 5, 6, Math.PI * 1.1, Math.PI * 1.9);
      ctx.arc(cx + 7, cy + 1, 5, Math.PI * 1.2, Math.PI * 0.2);
      ctx.lineTo(cx - 7, cy + 6);
      ctx.closePath();
      ctx.stroke();

      // Cloud smile arrow below
      ctx.strokeStyle = colors.c;
      ctx.beginPath();
      ctx.arc(cx, cy + 1, 10, Math.PI * 0.35, Math.PI * 0.75);
      ctx.stroke();
      // Arrow head
      ctx.fillStyle = colors.c;
      ctx.beginPath();
      ctx.moveTo(cx + 7, cy + 6);
      ctx.lineTo(cx + 10, cy + 5);
      ctx.lineTo(cx + 8, cy + 8);
      ctx.closePath();
      ctx.fill();
      break;

    case 'Docker':
      ctx.strokeStyle = colors.c;
      ctx.beginPath();
      // Whale body outline
      ctx.moveTo(cx - 15, cy + 4);
      ctx.quadraticCurveTo(cx - 15, cy - 2, cx - 4, cy - 2);
      ctx.quadraticCurveTo(cx + 8, cy - 2, cx + 13, cy + 2);
      ctx.quadraticCurveTo(cx + 17, cy + 4, cx + 17, cy + 8);
      ctx.quadraticCurveTo(cx + 10, cy + 10, cx - 15, cy + 10);
      ctx.closePath();
      ctx.stroke();
      
      // Whale tail
      ctx.beginPath();
      ctx.moveTo(cx - 15, cy + 4);
      ctx.lineTo(cx - 19, cy);
      ctx.lineTo(cx - 19, cy + 7);
      ctx.closePath();
      ctx.fillStyle = colors.c;
      ctx.fill();

      // Stacked cargo containers
      ctx.fillStyle = colors.p;
      ctx.fillRect(cx - 8, cy - 8, 3, 3);
      ctx.fillRect(cx - 3, cy - 8, 3, 3);
      ctx.fillRect(cx + 2, cy - 8, 3, 3);
      break;

    case 'Kubernetes':
      ctx.strokeStyle = colors.g;
      ctx.beginPath();
      for (let i = 0; i < 7; i++) {
        const angle = (i * Math.PI * 2) / 7 - Math.PI / 2;
        const rx = cx + 12 * Math.cos(angle);
        const ry = cy + 12 * Math.sin(angle);
        if (i === 0) ctx.moveTo(rx, ry);
        else ctx.lineTo(rx, ry);
      }
      ctx.closePath();
      ctx.stroke();

      for (let i = 0; i < 7; i++) {
        const angle = (i * Math.PI * 2) / 7 - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + 12 * Math.cos(angle), cy + 12 * Math.sin(angle));
        ctx.stroke();
      }

      ctx.fillStyle = colors.bg;
      ctx.beginPath();
      ctx.arc(cx, cy, 3.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = colors.g;
      ctx.stroke();
      break;

    case 'Terraform':
      ctx.strokeStyle = colors.p;
      ctx.lineWidth = 2.0;
      // Terraform exact isometric logo structure
      ctx.strokeRect(cx - 9, cy - 9, 6, 6);
      ctx.strokeRect(cx + 3, cy - 9, 6, 6);
      ctx.strokeRect(cx - 9, cy + 3, 6, 6);
      ctx.strokeRect(cx + 3, cy + 3, 6, 6);
      break;

    case 'Python':
      ctx.strokeStyle = colors.c;
      ctx.beginPath();
      ctx.arc(cx - 4, cy - 4, 5, Math.PI, Math.PI * 1.5);
      ctx.lineTo(cx + 2, cy - 9);
      ctx.arc(cx + 2, cy - 4, 5, Math.PI * 1.5, 0);
      ctx.lineTo(cx + 7, cy);
      ctx.arc(cx + 2, cy + 3, 5, 0, Math.PI * 0.5);
      ctx.lineTo(cx - 2, cy + 3);
      ctx.stroke();
      
      ctx.strokeStyle = colors.gold;
      ctx.beginPath();
      ctx.arc(cx + 4, cy + 4, 5, 0, Math.PI * 0.5);
      ctx.lineTo(cx - 2, cy + 9);
      ctx.arc(cx - 2, cy + 4, 5, Math.PI * 0.5, Math.PI);
      ctx.lineTo(cx - 7, cy);
      ctx.arc(cx - 2, cy - 3, 5, Math.PI, Math.PI * 1.5);
      ctx.lineTo(cx + 2, cy - 3);
      ctx.stroke();
      break;

    case 'Node.js':
      // Hexagon node
      ctx.strokeStyle = colors.g;
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (i * Math.PI) / 3 - Math.PI / 6;
        const hx = cx + 13 * Math.cos(angle);
        const hy = cy + 13 * Math.sin(angle);
        if (i === 0) ctx.moveTo(hx, hy);
        else ctx.lineTo(hx, hy);
      }
      ctx.closePath();
      ctx.stroke();

      // Inside leaf node instead of NODE text
      ctx.fillStyle = colors.g;
      ctx.beginPath();
      ctx.moveTo(cx, cy - 6);
      ctx.quadraticCurveTo(cx + 5, cy, cx, cy + 6);
      ctx.quadraticCurveTo(cx - 5, cy, cx, cy - 6);
      ctx.fill();
      break;

    case 'Git':
      ctx.strokeStyle = colors.p;
      ctx.beginPath();
      ctx.moveTo(cx - 3, cy - 10);
      ctx.lineTo(cx - 3, cy + 10);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.bezierCurveTo(cx - 3, cy, cx + 1, cy + 1, cx + 6, cy + 5);
      ctx.stroke();
      
      ctx.fillStyle = colors.p;
      ctx.beginPath(); ctx.arc(cx - 3, cy - 5, 2.5, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(cx - 3, cy + 5, 2.5, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(cx + 6, cy + 5, 2.5, 0, Math.PI * 2); ctx.fill();
      break;

    case 'Linux':
      // Silhouette of Tux penguin head & body
      ctx.fillStyle = colors.gold;
      ctx.strokeStyle = colors.gold;
      ctx.lineWidth = 1.5;
      
      // Body silhouette
      ctx.fillStyle = colors.c;
      ctx.beginPath();
      ctx.arc(cx, cy + 3, 7, Math.PI, 0, false);
      ctx.lineTo(cx + 7, cy + 9);
      ctx.lineTo(cx - 7, cy + 9);
      ctx.closePath();
      ctx.fill();

      // White tummy
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(cx, cy + 5, 4.5, 0, Math.PI * 2);
      ctx.fill();

      // Head
      ctx.fillStyle = colors.c;
      ctx.beginPath();
      ctx.arc(cx, cy - 3, 4, 0, Math.PI * 2);
      ctx.fill();

      // Beak (small gold triangle)
      ctx.fillStyle = colors.gold;
      ctx.beginPath();
      ctx.moveTo(cx - 2.5, cy - 3);
      ctx.lineTo(cx + 2.5, cy - 3);
      ctx.lineTo(cx, cy - 1.5);
      ctx.closePath();
      ctx.fill();

      // Wings
      ctx.strokeStyle = colors.c;
      ctx.beginPath();
      ctx.moveTo(cx - 5, cy + 1);
      ctx.quadraticCurveTo(cx - 9, cy + 4, cx - 7, cy + 7);
      ctx.moveTo(cx + 5, cy + 1);
      ctx.quadraticCurveTo(cx + 9, cy + 4, cx + 7, cy + 7);
      ctx.stroke();
      break;

    case 'AI':
      ctx.strokeStyle = colors.p;
      ctx.beginPath();
      ctx.arc(cx, cy, 3, 0, Math.PI * 2);
      ctx.fillStyle = colors.p;
      ctx.fill();
      
      const nodeCoords = [
        { x: cx - 11, y: cy - 9 },
        { x: cx + 11, y: cy - 9 },
        { x: cx - 11, y: cy + 9 },
        { x: cx + 11, y: cy + 9 }
      ];
      
      nodeCoords.forEach((node) => {
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(node.x, node.y);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.arc(node.x, node.y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = colors.c;
        ctx.fill();
      });
      break;

    case 'Shell':
    case 'Bash':
      ctx.strokeStyle = colors.g;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(cx - 8, cy - 6);
      ctx.lineTo(cx - 2, cy);
      ctx.lineTo(cx - 8, cy + 6);
      ctx.stroke();

      ctx.fillStyle = colors.g;
      ctx.fillRect(cx + 1, cy + 3, 6, 2.5);
      break;

    case 'CI/CD':
      ctx.strokeStyle = colors.c;
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      for (let i = 0; i < 100; i++) {
        const angle = (i * Math.PI * 2) / 100;
        const scale = 2 / (3 - Math.cos(2 * angle));
        const rx = cx + 13 * scale * Math.cos(angle);
        const ry = cy + 13 * scale * Math.sin(2 * angle) / 2;
        if (i === 0) ctx.moveTo(rx, ry);
        else ctx.lineTo(rx, ry);
      }
      ctx.closePath();
      ctx.stroke();
      break;

    case 'Selenium':
      // Web browser window frame
      ctx.strokeStyle = colors.p;
      ctx.lineWidth = 1.8;
      ctx.strokeRect(cx - 11, cy - 8, 22, 16);
      
      // Browser header line
      ctx.beginPath();
      ctx.moveTo(cx - 11, cy - 3);
      ctx.lineTo(cx + 11, cy - 3);
      ctx.stroke();
      
      // Little header dots
      ctx.fillStyle = colors.p;
      ctx.beginPath();
      ctx.arc(cx - 8, cy - 5, 1, 0, Math.PI * 2);
      ctx.arc(cx - 5, cy - 5, 1, 0, Math.PI * 2);
      ctx.fill();
      
      // Cursor pointer (clicking browser content area)
      ctx.strokeStyle = colors.c;
      ctx.fillStyle = colors.c;
      ctx.beginPath();
      ctx.moveTo(cx + 1, cy + 1);
      ctx.lineTo(cx + 6, cy + 6);
      ctx.lineTo(cx + 3, cy + 3);
      ctx.closePath();
      ctx.fill();
      break;

    default:
      ctx.fillStyle = colors.c;
      ctx.font = '8px monospace';
      ctx.fillText(tool.substring(0, 3), cx - 6, cy + 3);
  }
  ctx.restore();
};

export default function InteractiveBackground() {
  const canvasRef = useRef(null);
  const fgCanvasRef = useRef(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });

  useEffect(() => {
    const canvas = canvasRef.current;
    const fgCanvas = fgCanvasRef.current;
    if (!canvas || !fgCanvas) return;

    const ctx = canvas.getContext('2d');
    const fgCtx = fgCanvas.getContext('2d');
    if (!ctx || !fgCtx) return;

    let W, H;
    let particles = [];
    let nodes = [];
    let skillParticles = [];
    let time = 0;
    let animId;

    // Dynamic Theme Color Cache
    const themeColors = {
      c: '#00f5ff',
      p: '#b44fff',
      g: '#00e896',
      gold: '#ffd060',
      bg: '#020609'
    };

    // Pre-rendered offscreen canvases for each skill item to speed up draw loop
    const iconCache = {};
    const preRenderIcons = () => {
      SKILL_ITEMS.forEach(item => {
        const offscreen = document.createElement('canvas');
        offscreen.width = 128;
        offscreen.height = 128;
        const oCtx = offscreen.getContext('2d');
        if (oCtx) {
          // Pre-draw at 128x128 resolution for crisp rendering
          drawToolIcon(oCtx, 0, 0, 128, 128, item.text, themeColors);
        }
        iconCache[item.text] = offscreen;
      });
    };

    const updateThemeColors = () => {
      const styles = getComputedStyle(document.documentElement);
      themeColors.c = styles.getPropertyValue('--c').trim() || '#00f5ff';
      themeColors.p = styles.getPropertyValue('--p').trim() || '#b44fff';
      themeColors.g = styles.getPropertyValue('--g').trim() || '#00e896';
      themeColors.gold = styles.getPropertyValue('--gold').trim() || '#ffd060';
      themeColors.bg = styles.getPropertyValue('--bg').trim() || '#020609';
      
      // Update cache
      preRenderIcons();
    };

    window.addEventListener('theme-changed', updateThemeColors);
    updateThemeColors();

    const hexToRgb = (hex) => {
      const cleanHex = hex.replace('#', '').trim();
      if (cleanHex.length === 3) {
        const r = parseInt(cleanHex[0] + cleanHex[0], 16);
        const g = parseInt(cleanHex[1] + cleanHex[1], 16);
        const b = parseInt(cleanHex[2] + cleanHex[2], 16);
        return { r, g, b };
      }
      const bigint = parseInt(cleanHex, 16) || 0;
      const r = (bigint >> 16) & 255;
      const g = (bigint >> 8) & 255;
      const b = bigint & 255;
      return { r, g, b };
    };

    const getThemeColor = (origColor) => {
      if (origColor === '#ffd060') return themeColors.gold;
      if (origColor === '#00f5ff') return themeColors.c;
      if (origColor === '#00e896') return themeColors.g;
      if (origColor === '#b44fff') return themeColors.p;
      return themeColors.c; // fallback
    };

    const resize = () => {
      W = canvas.width = fgCanvas.width = window.innerWidth;
      H = canvas.height = fgCanvas.height = window.innerHeight;
      initParticles();
      initSkills();
    };

    const initParticles = () => {
      // Background star field
      particles = Array.from({ length: 90 }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.5 + 0.4,
        a: Math.random(),
        sp: Math.random() * 0.005 + 0.002,
        colorType: Math.random() > 0.7 ? 'p' : 'c'
      }));

      // Background network constellations
      nodes = Array.from({ length: 30 }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.2,
        vy: (Math.random() - 0.5) * 0.2
      }));
    };

    const initSkills = () => {
      // Skills snowfall particles - falling layout
      skillParticles = Array.from({ length: 32 }, () => {
        const item = SKILL_ITEMS[Math.floor(Math.random() * SKILL_ITEMS.length)];
        const baseVy = (Math.random() * 0.4 + 0.2) * 0.9; // Falling speed: decreased by 10%
        return {
          ...item,
          x: Math.random() * W,
          y: Math.random() * H,
          size: Math.random() * 12 + 52,      // Larger sizes (52px to 64px)
          alpha: Math.random() * 0.12 + 0.12,  // subtle background transparency
          baseVy,
          vy: baseVy
        };
      });
    };

    resize();
    window.addEventListener('resize', resize);

    const handleMouseMove = (e) => {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
    };

    const handleTouchMove = (e) => {
      if (e.touches[0]) {
        mouseRef.current.x = e.touches[0].clientX;
        mouseRef.current.y = e.touches[0].clientY;
      }
    };

    const handleMouseLeave = () => {
      mouseRef.current.x = -1000;
      mouseRef.current.y = -1000;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('touchmove', handleTouchMove, { passive: true });
    window.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseleave', handleMouseLeave);

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      fgCtx.clearRect(0, 0, W, H);
      time += 0.005;

      const mouse = mouseRef.current;
      const rgbC = hexToRgb(themeColors.c);
      const rgbP = hexToRgb(themeColors.p);
      const rgbG = hexToRgb(themeColors.g);

      // 1. Moving Aurora Gradient Blobs
      const blobs = [
        {
          x: W * 0.25 + Math.sin(time * 0.4) * W * 0.08,
          y: H * 0.3 + Math.cos(time * 0.3) * H * 0.08,
          r: W * 0.35,
          c1: `rgba(${rgbC.r}, ${rgbC.g}, ${rgbC.b}, 0.035)`,
          c2: 'transparent'
        },
        {
          x: W * 0.75 + Math.cos(time * 0.35) * W * 0.06,
          y: H * 0.7 + Math.sin(time * 0.5) * H * 0.07,
          r: W * 0.3,
          c1: `rgba(${rgbP.r}, ${rgbP.g}, ${rgbP.b}, 0.035)`,
          c2: 'transparent'
        },
        {
          x: W * 0.5 + Math.sin(time * 0.6) * W * 0.08,
          y: H * 0.55 + Math.cos(time * 0.4) * H * 0.06,
          r: W * 0.25,
          c1: `rgba(${rgbG.r}, ${rgbG.g}, ${rgbG.b}, 0.02)`,
          c2: 'transparent'
        }
      ];

      blobs.forEach((b) => {
        const g = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.r);
        g.addColorStop(0, b.c1);
        g.addColorStop(1, b.c2);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.fill();
      });

      // 2. Mouse Reactive Ripple Glow
      if (mouse.x > -500 && mouse.y > -500) {
        const mr = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 160);
        mr.addColorStop(0, `rgba(${rgbC.r}, ${rgbC.g}, ${rgbC.b}, 0.05)`);
        mr.addColorStop(1, 'transparent');
        ctx.fillStyle = mr;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, 160, 0, Math.PI * 2);
        ctx.fill();
      }

      // 3. Network Nodes & Connections
      nodes.forEach((n) => {
        n.x += n.vx;
        n.y += n.vy;

        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;

        // Mild mouse pull
        if (mouse.x > -500 && mouse.y > -500) {
          const dx = mouse.x - n.x;
          const dy = mouse.y - n.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 180) {
            n.x += dx * 0.002;
            n.y += dy * 0.002;
          }
        }
      });

      nodes.forEach((a, i) => {
        nodes.slice(i + 1).forEach((b) => {
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < 160) {
            ctx.strokeStyle = `rgba(${rgbC.r}, ${rgbC.g}, ${rgbC.b}, ${0.1 * (1 - d / 160)})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        });
      });

      // 4. Star Particles (Drifting backdrop)
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = W;
        if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H;
        if (p.y > H) p.y = 0;

        // Mouse repel
        if (mouse.x > -500 && mouse.y > -500) {
          const dx = p.x - mouse.x;
          const dy = p.y - mouse.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < 90) {
            p.x += dx * 0.02;
            p.y += dy * 0.02;
          }
        }

        p.a += p.sp;
        if (p.a > 1) p.a = 0;

        const alpha = Math.sin(p.a * Math.PI) * 0.7 + 0.1;
        ctx.save();
        ctx.globalAlpha = alpha;
        const starColorHex = p.colorType === 'p' ? themeColors.p : themeColors.c;
        const rgbStar = hexToRgb(starColorHex);
        ctx.fillStyle = `rgba(${rgbStar.r}, ${rgbStar.g}, ${rgbStar.b}, 1)`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      });

      // 5. Falling Backdrop Skills Logos (Slow down on hover, wrap around bottom, foreground layering)
      skillParticles.forEach((p) => {
        // Mouse hover logic (radius matches larger icon size)
        let isHovered = false;
        const hoverRadius = p.size * 0.8;
        if (mouse.x > -500 && mouse.y > -500) {
          const dx = p.x - mouse.x;
          const dy = p.y - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < hoverRadius) {
            isHovered = true;
          }
        }

        // Slow down if hovered, else return to base speed
        const targetVy = isHovered ? p.baseVy * 0.15 : p.baseVy;
        p.vy = p.vy + (targetVy - p.vy) * 0.15; // Smooth interpolation
        p.y += p.vy;

        // Wrap around at the bottom
        if (p.y > H + p.size / 2) {
          p.y = -p.size / 2;
          p.x = Math.random() * W;
        }

        // Determine targets based on layer
        const targetCtx = isHovered ? fgCtx : ctx;
        const renderSize = isHovered ? p.size * 1.25 : p.size;
        const finalAlpha = isHovered ? 0.95 : p.alpha;
        const activeColor = getThemeColor(p.color);

        targetCtx.save();
        targetCtx.globalAlpha = finalAlpha;

        if (isHovered) {
          targetCtx.shadowBlur = 25;
          targetCtx.shadowColor = activeColor;
        }

        // Draw textless vector logo shape from pre-rendered cache
        const cachedCanvas = iconCache[p.text];
        if (cachedCanvas) {
          targetCtx.drawImage(
            cachedCanvas, 
            p.x - renderSize / 2, 
            p.y - renderSize / 2, 
            renderSize, 
            renderSize
          );
        } else {
          drawToolIcon(
            targetCtx, 
            p.x - renderSize / 2, 
            p.y - renderSize / 2, 
            renderSize, 
            renderSize, 
            p.text, 
            themeColors
          );
        }
        targetCtx.restore();

        // Tooltip rendering on the crisp foreground layer
        if (isHovered) {
          fgCtx.save();
          fgCtx.font = `10px 'Share Tech Mono', monospace`;
          fgCtx.fillStyle = themeColors.c;
          fgCtx.shadowBlur = 8;
          fgCtx.shadowColor = themeColors.c;
          fgCtx.globalAlpha = 0.95;

          const labelText = p.label;
          fgCtx.textAlign = 'center';
          const textWidth = fgCtx.measureText(labelText).width;
          
          // Draw neat bounding glass tooltip card
          fgCtx.fillStyle = 'rgba(2, 6, 9, 0.92)';
          const activeRgb = hexToRgb(themeColors.c);
          fgCtx.strokeStyle = `rgba(${activeRgb.r}, ${activeRgb.g}, ${activeRgb.b}, 0.6)`;
          fgCtx.lineWidth = 1;
          fgCtx.beginPath();
          fgCtx.roundRect(p.x - textWidth / 2 - 8, p.y - renderSize / 2 - 25, textWidth + 16, 18, 4);
          fgCtx.fill();
          fgCtx.stroke();

          fgCtx.fillStyle = themeColors.c;
          fgCtx.fillText(labelText, p.x, p.y - renderSize / 2 - 13);
          fgCtx.restore();
        }
      });

      animId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('theme-changed', updateThemeColors);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <>
      <canvas ref={canvasRef} id="bg-canvas" />
      <canvas ref={fgCanvasRef} id="fg-canvas" />
      <div className="grid-overlay" />
      <div className="noise" />
      <div className="scanlines" />
    </>
  );
}
