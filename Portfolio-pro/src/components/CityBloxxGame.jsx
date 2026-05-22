import { useEffect, useRef, useState } from 'react';
import { RefreshCw, Award, Server, Trophy, User } from 'lucide-react';
import './CityBloxxGame.css';

// Developer skills represented by icons
const RESUME_TOOLS = [
  'AWS', 'Docker', 'Kubernetes', 'Terraform', 'Python',
  'Node.js', 'Git', 'Linux', 'AI', 'Shell', 'CI/CD'
];

// Helper to draw clean vector tool icons on canvas
const drawToolIcon = (ctx, x, y, w, h, tool, colors = { c: '#00f5ff', p: '#b44fff', g: '#00e896', gold: '#ffd060', bg: '#020609' }) => {
  ctx.save();
  ctx.translate(x, y);

  const cx = w / 2;
  const cy = h / 2;

  ctx.lineWidth = 1.8;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  switch (tool) {
    case 'AWS':
      // Amazon cloud outline
      ctx.strokeStyle = colors.gold;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx - 7, cy + 1, 5, Math.PI * 0.8, Math.PI * 1.8);
      ctx.arc(cx, cy - 5, 6, Math.PI * 1.1, Math.PI * 1.9);
      ctx.arc(cx + 7, cy + 1, 5, Math.PI * 1.2, Math.PI * 0.2);
      ctx.lineTo(cx - 7, cy + 6);
      ctx.closePath();
      ctx.stroke();

      // Cloud smile arrow below
      ctx.strokeStyle = colors.c;
      ctx.lineWidth = 1.5;
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
      ctx.lineWidth = 1.8;
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
      // A small gear representation
      ctx.strokeStyle = colors.c;
      ctx.beginPath();
      ctx.arc(cx, cy, 4, 0, Math.PI * 2);
      ctx.stroke();
      for (let i = 0; i < 8; i++) {
        const angle = (i * Math.PI) / 4;
        ctx.beginPath();
        ctx.moveTo(cx + 4 * Math.cos(angle), cy + 4 * Math.sin(angle));
        ctx.lineTo(cx + 7 * Math.cos(angle), cy + 7 * Math.sin(angle));
        ctx.stroke();
      }
      break;
  }
  ctx.restore();
};

// Blocks required per level before triggering Level Complete
const BLOCKS_PER_LEVEL = 8;

// Level configs — each level is harder
const LEVEL_CONFIGS = [
  { id: 1, name: 'BOOT UP',      speed: 1.0,  sway:  0, gap:  0,  blockSize: 44 },
  { id: 2, name: 'STAGING',     speed: 1.3,  sway: 18, gap:  0,  blockSize: 42 },
  { id: 3, name: 'PRODUCTION',  speed: 1.6,  sway: 35, gap: 50,  blockSize: 38 },
  { id: 4, name: 'HIGH LOAD',   speed: 1.9,  sway: 55, gap: 80,  blockSize: 34 },
  { id: 5, name: 'CRITICAL',    speed: 2.2,  sway: 70, gap: 100, blockSize: 30 },
  { id: 6, name: 'ENTERPRISE',  speed: 2.6,  sway: 85, gap: 120, blockSize: 28 },
];

const getLevelConfig = (levelNum) => LEVEL_CONFIGS[Math.min(levelNum - 1, LEVEL_CONFIGS.length - 1)];


export default function CityBloxxGame() {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  
  // Game states
  const [score, setScore] = useState(0);
  const [floors, setFloors] = useState(0);
  const [combo, setCombo] = useState(0);
  const [lives, setLives] = useState(3);
  const [gameOver, setGameOver] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [levelNum, setLevelNum] = useState(1);
  const [levelComplete, setLevelComplete] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [nameSaved, setNameSaved] = useState(false);
  const [leaderboard, setLeaderboard] = useState(() => {
    try { return JSON.parse(localStorage.getItem('citybloxx_leaderboard') || '[]'); }
    catch { return []; }
  });
  
  const [highScore, setHighScore] = useState(() => {
    try {
      return parseInt(localStorage.getItem('citybloxx_highscore') || '0', 10);
    } catch {
      return 0;
    }
  });

  const saveToLeaderboard = (name, sc) => {
    const entry = { name: name.trim().toUpperCase() || 'ANON', score: sc, date: new Date().toLocaleDateString() };
    const updated = [...leaderboard, entry]
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);
    setLeaderboard(updated);
    try { localStorage.setItem('citybloxx_leaderboard', JSON.stringify(updated)); } catch {}
  };

  const handleNameSubmit = (sc) => {
    if (!nameInput.trim()) return;
    saveToLeaderboard(nameInput, sc);
    setNameSaved(true);
  };

  const clearLeaderboard = () => {
    setLeaderboard([]);
    setHighScore(0);
    try {
      localStorage.removeItem('citybloxx_leaderboard');
      localStorage.removeItem('citybloxx_highscore');
    } catch {}
  };

  const startGame = () => {
    setIsPlaying(true);
    setGameOver(false);
    setLevelComplete(false);
    setScore(0);
    setFloors(0);
    setCombo(0);
    setLives(3);
    setLevelNum(1);
    window.dispatchEvent(new CustomEvent('citybloxx_reset_game', { detail: { level: 1 } }));
  };

  const advanceLevel = (currentLives, currentScore, nextLevel) => {
    setLevelComplete(false);
    setLevelNum(nextLevel);
    setFloors(0);
    window.dispatchEvent(new CustomEvent('citybloxx_next_level', { detail: { level: nextLevel, lives: currentLives, score: currentScore } }));
  };

  const stateRef = useRef({
    isPlaying: true,
    gameOver: false,
    levelComplete: false,
    score: 0,
    floors: 0,
    combo: 0,
    lives: 3
  });

  useEffect(() => {
    stateRef.current = {
      isPlaying,
      gameOver,
      levelComplete,
      score,
      floors,
      combo,
      lives
    };
  }, [isPlaying, gameOver, levelComplete, score, floors, combo, lives]);

  const playSound = (type) => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      const now = ctx.currentTime;

      if (type === 'drop') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(160, now);
        osc.frequency.exponentialRampToValueAtTime(320, now + 0.12);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
        osc.start(now);
        osc.stop(now + 0.12);
      } else if (type === 'perfect') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, now); // D5
        osc.frequency.setValueAtTime(880, now + 0.07); // A5
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);
        osc.start(now);
        osc.stop(now + 0.25);
      } else if (type === 'land') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(392, now); // G4
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
        osc.start(now);
        osc.stop(now + 0.15);
      } else if (type === 'miss') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(180, now);
        osc.frequency.linearRampToValueAtTime(90, now + 0.25);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);
        osc.start(now);
        osc.stop(now + 0.25);
      } else if (type === 'gameover') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(180, now);
        osc.frequency.setValueAtTime(150, now + 0.2);
        osc.frequency.setValueAtTime(120, now + 0.4);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.7);
        osc.start(now);
        osc.stop(now + 0.7);
      }
    } catch {}
  };

  const triggerDrop = () => {
    if (!stateRef.current.isPlaying || stateRef.current.gameOver || stateRef.current.levelComplete) return;
    window.dispatchEvent(new CustomEvent('citybloxx_drop_block'));
  };


  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animFrameId;

    // Game physics constants
    const PIVOT_Y = 15;
    const ROPE_LENGTH = 120;
    const GRAVITY = 0.55;
    const SWING_SPEED = 0.0035;
    const SWING_MAX_ANGLE = 0.45;

    // Dynamic Theme Color Cache
    const themeColors = {
      c: '#00f5ff',
      p: '#b44fff',
      g: '#00e896',
      gold: '#ffd060',
      bg: '#020609'
    };

    const updateColors = () => {
      const styles = getComputedStyle(document.documentElement);
      themeColors.c = styles.getPropertyValue('--c').trim() || '#00f5ff';
      themeColors.p = styles.getPropertyValue('--p').trim() || '#b44fff';
      themeColors.g = styles.getPropertyValue('--g').trim() || '#00e896';
      themeColors.gold = styles.getPropertyValue('--gold').trim() || '#ffd060';
      themeColors.bg = styles.getPropertyValue('--bg').trim() || '#020609';
    };

    window.addEventListener('theme-changed', updateColors);
    updateColors();

    let width = canvas.width = canvas.parentElement?.clientWidth || 350;
    let height = canvas.height = canvas.parentElement?.clientHeight || 550;

    let blocks = [];
    let topBlockXOffset = 0;
    
    // Crane pendulum parameters
    let pivotX = width / 2;
    let swingAngle = 0;
    let hookX = width / 2;
    let hookY = PIVOT_Y + ROPE_LENGTH;
    let prevHookX = width / 2; // For calculating release inertia
    
    let fallingBlock = null;
    let particles = [];
    let scorePopups = [];
    let scale = 1.0;
    let targetScale = 1.0;
    let pivotY = PIVOT_Y;

    // current level config (updated when next_level event fires)
    let currentLevelConfig = getLevelConfig(1);

    const initGame = (levelNum = 1) => {
      currentLevelConfig = getLevelConfig(levelNum);
      blocks = [
        {
          x: width / 2 - currentLevelConfig.blockSize / 2,
          y: height - currentLevelConfig.blockSize - 20,
          w: currentLevelConfig.blockSize,
          h: currentLevelConfig.blockSize,
          tool: 'AWS',
          stable: true
        }
      ];
      fallingBlock = null;
      scale = 1.0;
      targetScale = 1.0;
      pivotY = PIVOT_Y;
      particles = [];
      scorePopups = [];
      topBlockXOffset = 0;
    };

    initGame();

    const resizeGame = (newW, newH) => {
      const prevW = width;
      const prevH = height;

      width = canvas.width = newW || canvas.parentElement?.clientWidth || 350;
      height = canvas.height = newH || canvas.parentElement?.clientHeight || 550;

      const diffX = width / 2 - prevW / 2;
      const diffY = height - prevH;

      blocks.forEach(b => {
        b.x += diffX;
        b.y += diffY;
      });

      pivotX = width / 2;
    };

    // Use ResizeObserver for reliable dimensions settlement
    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width: entryW, height: entryH } = entry.contentRect;
        if (entryW > 0 && entryH > 0) {
          resizeGame(Math.round(entryW), Math.round(entryH));
        }
      }
    });

    if (canvas.parentElement) {
      resizeObserver.observe(canvas.parentElement);
    }

    const handleDropRequest = () => {
      if (fallingBlock && !fallingBlock.falling) {
        fallingBlock.falling = true;
        fallingBlock.vy = 0.5;
        fallingBlock.vx = hookX - prevHookX;
        const cos = Math.cos(swingAngle);
        const sin = Math.sin(swingAngle);
        fallingBlock.x = hookX - (currentLevelConfig.blockSize / 2) * cos - 11 * sin;
        fallingBlock.y = hookY - (currentLevelConfig.blockSize / 2) * sin + 11 * cos;
        fallingBlock.rotation = swingAngle;
        playSound('drop');
      }
    };

    window.addEventListener('citybloxx_drop_block', handleDropRequest);
    window.addEventListener('citybloxx_reset_game', (e) => initGame(e?.detail?.level || 1));

    const handleNextLevel = (e) => {
      const nextLvl = e?.detail?.level || 1;
      initGame(nextLvl);
    };
    window.addEventListener('citybloxx_next_level', handleNextLevel);

    const handleGlobalClick = (e) => {
      if (!stateRef.current.isPlaying || stateRef.current.gameOver || stateRef.current.levelComplete) return;
      if (e.target.closest('.game-control-btn') || e.target.closest('a') || e.target.closest('button') || e.target.closest('input')) {
        return;
      }
      handleDropRequest();
    };
    window.addEventListener('click', handleGlobalClick);

    const spawnParticles = (x, y, color) => {
      for (let i = 0; i < 12; i++) {
        particles.push({
          x,
          y,
          vx: (Math.random() - 0.5) * 5,
          vy: (Math.random() - 0.5) * 5 - 1.5,
          radius: Math.random() * 2 + 1,
          color,
          alpha: 1,
          decay: Math.random() * 0.05 + 0.03
        });
      }
    };

    const spawnScorePopup = (x, y, text, isPerfect = false) => {
      scorePopups.push({
        x,
        y,
        text,
        isPerfect,
        alpha: 1,
        vy: -1
      });
    };

    const draw = (timestamp) => {
      ctx.clearRect(0, 0, width, height);

      const activeState = stateRef.current;

      if (activeState.isPlaying && !activeState.levelComplete) {
        const topBlock = blocks[blocks.length - 1];
        const time = timestamp || 0;

        // 1. Crane pendulum using current level config
        swingAngle = Math.sin(time * SWING_SPEED * currentLevelConfig.speed) * SWING_MAX_ANGLE;
        pivotX = width / 2 + Math.sin(time * 0.0015) * currentLevelConfig.sway;
        
        prevHookX = hookX;
        hookX = pivotX + ROPE_LENGTH * Math.sin(swingAngle);
        hookY = pivotY + ROPE_LENGTH * Math.cos(swingAngle);

        // 2. Prepare next hanging block
        if (!fallingBlock) {
          const randomTool = RESUME_TOOLS[Math.floor(Math.random() * RESUME_TOOLS.length)];
          fallingBlock = {
            x: hookX - currentLevelConfig.blockSize / 2,
            y: hookY,
            w: currentLevelConfig.blockSize,
            h: currentLevelConfig.blockSize,
            vx: 0, vy: 0, falling: false,
            tool: randomTool, rotation: 0
          };
        } else if (!fallingBlock.falling) {
          fallingBlock.w = currentLevelConfig.blockSize;
          fallingBlock.h = currentLevelConfig.blockSize;
          fallingBlock.x = hookX - fallingBlock.w / 2;
          fallingBlock.y = hookY;
          fallingBlock.rotation = swingAngle;
        }

        // 3. Dynamic scale & pivotY follow
        const min_distance = ROPE_LENGTH + currentLevelConfig.blockSize + 40 + currentLevelConfig.gap;
        const topBlockY = topBlock ? topBlock.y : height - 20;
        const targetPivotY = Math.min(PIVOT_Y, topBlockY - min_distance);
        pivotY += (targetPivotY - pivotY) * 0.1;

        targetScale = Math.min(1.0, height / (height - pivotY + 20));
        scale += (targetScale - scale) * 0.1;

        ctx.save();
        // Scale everything from the bottom-center of the canvas to fit the window
        ctx.translate(width / 2, height);
        ctx.scale(scale, scale);
        ctx.translate(-width / 2, -height);

        // Tower sways based on offsets
        let sway = 0;
        if (blocks.length > 2) {
          const totalOffset = blocks.reduce((acc, b, index) => {
            if (index === 0) return acc;
            return acc + Math.abs(b.x - blocks[index - 1].x);
          }, 0);
          const maxSwayFactor = Math.min(totalOffset * 0.05, 15);
          sway = Math.sin(time * 0.002) * maxSwayFactor;
        }

        // 4. Render Stacking Blocks
        blocks.forEach((block, index) => {
          let renderX = block.x;
          if (index > 0) {
            const heightFactor = index / blocks.length;
            renderX += sway * heightFactor;
          }

          ctx.save();
          ctx.translate(renderX, block.y);

          // Glass framework
          ctx.strokeStyle = block.stable ? themeColors.c : themeColors.p;
          ctx.lineWidth = block.stable ? 1.5 : 1;
          ctx.fillStyle = 'rgba(6, 14, 32, 0.88)';
          
          ctx.beginPath();
          ctx.roundRect(0, 0, block.w, block.h, 6);
          ctx.fill();
          ctx.stroke();

          // Sub-grid lines inside card
          ctx.strokeStyle = block.stable ? 'rgba(0, 245, 255, 0.12)' : 'rgba(180, 79, 255, 0.1)';
          ctx.strokeRect(3, 3, block.w - 6, block.h - 6);

          // Draw theme-reactive skills icon
          drawToolIcon(ctx, 0, 0, block.w, block.h, block.tool, themeColors);

          // Draw small stack bracket/ring on top of block
          if (index === blocks.length - 1) {
            ctx.strokeStyle = themeColors.c;
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.arc(block.w / 2, 0, 5, Math.PI, 0);
            ctx.stroke();
          }

          ctx.restore();
        });

        // 5. Update Falling Block Physics
        if (fallingBlock && fallingBlock.falling) {
          fallingBlock.vy += GRAVITY;
          fallingBlock.y += fallingBlock.vy;
          fallingBlock.x += fallingBlock.vx;
          fallingBlock.vx *= 0.95;
          fallingBlock.rotation *= 0.92;

          const targetY = topBlock.y - fallingBlock.h;

          if (fallingBlock.y >= targetY) {
            fallingBlock.y = targetY;
            const dx = (fallingBlock.x + fallingBlock.w / 2) - (topBlock.x + topBlock.w / 2);
            const threshold = fallingBlock.w * 0.85;

            if (Math.abs(dx) <= threshold) {
              const isPerfect = Math.abs(dx) <= 5.5;
              let finalX = fallingBlock.x;

              if (isPerfect) {
                finalX = topBlock.x + (topBlock.w - fallingBlock.w) / 2; // lock to center
                const newCombo = activeState.combo + 1;
                setCombo(newCombo);
                setScore(prev => prev + 100 * newCombo);
                spawnParticles(finalX + fallingBlock.w / 2, targetY + fallingBlock.h / 2, themeColors.c);
                spawnScorePopup(finalX + fallingBlock.w / 2, targetY, `PERFECT! x${newCombo}`, true);
                playSound('perfect');
              } else {
                setCombo(0);
                setScore(prev => prev + 40);
                spawnParticles(finalX + fallingBlock.w / 2, targetY + fallingBlock.h / 2, themeColors.p);
                spawnScorePopup(finalX + fallingBlock.w / 2, targetY, '+40', false);
                playSound('land');
              }

              blocks.push({
                x: finalX, y: targetY,
                w: fallingBlock.w, h: fallingBlock.h,
                tool: fallingBlock.tool, stable: isPerfect
              });

              // Count placed blocks (excluding base block)
              const placedCount = blocks.length - 1;
              setFloors(placedCount);
              fallingBlock = null;

              // Level complete every BLOCKS_PER_LEVEL placed blocks
              if (placedCount > 0 && placedCount % BLOCKS_PER_LEVEL === 0) {
                setLevelComplete(true);
              }
            } else {
              // Collapse/Miss
              spawnParticles(fallingBlock.x + fallingBlock.w / 2, fallingBlock.y + fallingBlock.h / 2, '#ff3b30');
              spawnScorePopup(fallingBlock.x + fallingBlock.w / 2, fallingBlock.y, 'MISS!', false);
              playSound('miss');
              fallingBlock = null;

              const remainingLives = activeState.lives - 1;
              setLives(remainingLives);

              if (remainingLives <= 0) {
                setGameOver(true);
                setNameInput('');
                setNameSaved(false);
                playSound('gameover');
                if (activeState.score > highScore) {
                  setHighScore(activeState.score);
                  try {
                    localStorage.setItem('citybloxx_highscore', activeState.score.toString());
                  } catch {}
                }
              }
            }
          }
        }

        // Draw Active Falling Block
        if (fallingBlock && fallingBlock.falling) {
          ctx.save();
          ctx.translate(fallingBlock.x, fallingBlock.y);
          ctx.translate(fallingBlock.w / 2, fallingBlock.h / 2);
          ctx.rotate(fallingBlock.rotation);
          ctx.translate(-fallingBlock.w / 2, -fallingBlock.h / 2);

          ctx.strokeStyle = themeColors.c;
          ctx.fillStyle = 'rgba(6, 14, 32, 0.88)';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.roundRect(0, 0, fallingBlock.w, fallingBlock.h, 6);
          ctx.fill();
          ctx.stroke();

          ctx.strokeStyle = 'rgba(0, 245, 255, 0.12)';
          ctx.strokeRect(3, 3, fallingBlock.w - 6, fallingBlock.h - 6);

          drawToolIcon(ctx, 0, 0, fallingBlock.w, fallingBlock.h, fallingBlock.tool, themeColors);

          ctx.strokeStyle = themeColors.c;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(fallingBlock.w / 2, 0, 5, Math.PI, 0);
          ctx.stroke();

          ctx.restore();
        }

        // 6. Particle / Score popup updates
        for (let i = particles.length - 1; i >= 0; i--) {
          const p = particles[i];
          p.x += p.vx; p.y += p.vy;
          p.alpha -= p.decay;
          if (p.alpha <= 0) { particles.splice(i, 1); continue; }
          ctx.save();
          ctx.fillStyle = p.color;
          ctx.globalAlpha = p.alpha;
          ctx.beginPath(); ctx.arc(p.x, p.y, p.radius, 0, Math.PI*2); ctx.fill();
          ctx.restore();
        }

        for (let i = scorePopups.length - 1; i >= 0; i--) {
          const pop = scorePopups[i];
          pop.y += pop.vy;
          pop.alpha -= 0.025;
          if (pop.alpha <= 0) { scorePopups.splice(i, 1); continue; }
          ctx.save();
          ctx.fillStyle = pop.isPerfect ? themeColors.c : themeColors.p;
          ctx.font = pop.isPerfect ? "bold 11px sans-serif" : "bold 9px sans-serif";
          ctx.textAlign = 'center';
          ctx.globalAlpha = pop.alpha;
          ctx.fillText(pop.text, pop.x, pop.y);
          ctx.restore();
        }

        // 7. Pulley wheel at top
        ctx.save();
        ctx.translate(pivotX, pivotY);
        ctx.fillStyle = themeColors.bg;
        ctx.strokeStyle = themeColors.c;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(0, 0, 2, 0, Math.PI * 2);
        ctx.fillStyle = themeColors.c;
        ctx.fill();
        ctx.restore();

        // 8. Swinging Rope
        ctx.strokeStyle = themeColors.c;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(pivotX, pivotY);
        ctx.lineTo(hookX, hookY);
        ctx.stroke();

        // Draw Active Swinging Block
        if (fallingBlock && !fallingBlock.falling) {
          ctx.save();
          ctx.translate(hookX, hookY);
          ctx.rotate(swingAngle);
          ctx.translate(-fallingBlock.w / 2, 11);

          ctx.strokeStyle = themeColors.c;
          ctx.fillStyle = 'rgba(6, 14, 32, 0.88)';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.roundRect(0, 0, fallingBlock.w, fallingBlock.h, 6);
          ctx.fill();
          ctx.stroke();

          ctx.strokeStyle = 'rgba(0, 245, 255, 0.12)';
          ctx.strokeRect(3, 3, fallingBlock.w - 6, fallingBlock.h - 6);

          drawToolIcon(ctx, 0, 0, fallingBlock.w, fallingBlock.h, fallingBlock.tool, themeColors);

          ctx.strokeStyle = themeColors.c;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(fallingBlock.w / 2, 0, 5, Math.PI, 0);
          ctx.stroke();

          ctx.restore();
        }

        // 9. Mechanical Double-curved hook
        ctx.save();
        ctx.translate(hookX, hookY);
        ctx.rotate(swingAngle);
        
        ctx.strokeStyle = themeColors.c;
        ctx.lineWidth = 2;
        
        ctx.beginPath();
        ctx.arc(0, -2, 3, 0, Math.PI * 2);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, 6);
        ctx.arc(-3, 6, 3, 0, Math.PI * 0.7);
        ctx.moveTo(0, 6);
        ctx.arc(3, 6, 3, Math.PI, Math.PI * 0.3);
        ctx.stroke();
        
        ctx.restore();

        ctx.restore();
      }

      animFrameId = requestAnimationFrame(draw);
    };

    animFrameId = requestAnimationFrame(draw);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('theme-changed', updateColors);
      window.removeEventListener('resize', resizeGame);
      window.removeEventListener('click', handleGlobalClick);
      window.removeEventListener('citybloxx_drop_block', handleDropRequest);
      window.removeEventListener('citybloxx_reset_game', initGame);
      cancelAnimationFrame(animFrameId);
    };
  }, []);

  return (
    <div className="citybloxx-container" ref={containerRef}>
      {/* HUD metrics header bar */}
      <div className="game-hud">
        <div className="hud-left">
          <div className="hud-metric">
            <span className="hud-label">HEIGHT</span>
            <span className="hud-value text-cyan">{floors} Fl</span>
          </div>
          <div className="hud-metric">
            <span className="hud-label">SCORE</span>
            <span className="hud-value text-magenta">{score}</span>
          </div>
          {combo > 0 && (
            <div className="hud-metric">
              <span className="hud-label">COMBO</span>
              <span className="hud-value text-yellow">x{combo}</span>
            </div>
          )}
        </div>

        <div className="hud-center">
          <div className="hud-lives-row">
            {[...Array(3)].map((_, i) => (
              <Server 
                key={i} 
                size={12} 
                className={`server-icon ${i < lives ? 'active' : ''}`} 
              />
            ))}
          </div>
        </div>

        <div className="hud-right">
          <div className="hud-metric" style={{ marginRight: '8px' }}>
            <span className="hud-label">LEVEL</span>
            <span className="hud-value text-yellow">{levelNum}</span>
          </div>
          {isPlaying && !gameOver && (
            <button className="hud-icon-btn reset" onClick={startGame} title="Restart Engine">
              <RefreshCw size={12} />
            </button>
          )}
        </div>
      </div>

      {/* GAME CANVAS */}
      <div className="canvas-wrapper" onClick={triggerDrop}>
        <canvas ref={canvasRef} id="citybloxx-canvas" />

        {/* OVERLAYS */}
        {gameOver && (
          <div className="game-overlay game-over-overlay">
            <div className="overlay-content">
              <h2 className="text-red font-display">TOWER COLLAPSED</h2>
              <p>Height: <strong className="text-cyan">{floors} floors</strong></p>
              <p>Score: <strong className="text-magenta">{score}</strong></p>

              {!nameSaved ? (
                <div className="name-entry-block">
                  <p className="name-prompt">Enter your name to save score:</p>
                  <div className="name-input-row">
                    <input
                      className="name-input"
                      type="text"
                      maxLength={12}
                      placeholder="YOUR NAME"
                      value={nameInput}
                      onChange={e => setNameInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleNameSubmit(score)}
                      autoFocus
                    />
                    <button
                      className="game-control-btn name-save-btn"
                      onClick={() => handleNameSubmit(score)}
                    >SAVE</button>
                  </div>
                </div>
              ) : (
                <div className="leaderboard-block">
                  <div className="lb-header">
                    <p className="lb-title">🏆 TOP SCORES</p>
                    <button className="lb-clear-btn" onClick={clearLeaderboard}>CLEAR DB</button>
                  </div>
                  {leaderboard.length === 0 ? (
                    <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.7rem', marginTop: '6px' }}>No records yet.</p>
                  ) : leaderboard.slice(0, 5).map((e, i) => (
                    <div key={i} className={`lb-row ${i === 0 ? 'lb-top' : ''}`}>
                      <span className="lb-rank">#{i + 1}</span>
                      <span className="lb-name">{e.name}</span>
                      <span className="lb-score text-cyan">{e.score}</span>
                    </div>
                  ))}
                </div>
              )}

              <button className="game-control-btn primary-btn font-display" onClick={startGame} style={{ marginTop: '14px' }}>
                RECONSTRUCT
              </button>
            </div>
          </div>
        )}

        {/* LEVEL COMPLETE OVERLAY */}
        {levelComplete && !gameOver && (
          <div className="game-overlay level-complete-overlay">
            <div className="overlay-content">
              <div className="lc-badge">⚡ LEVEL {levelNum} COMPLETE</div>
              <h2 className="text-yellow font-display">SYSTEM UPGRADED</h2>
              <p>Floors stacked: <strong className="text-cyan">{floors}</strong></p>
              <p>Score: <strong className="text-magenta">{score}</strong></p>
              <p>Lives remaining: <strong className="text-cyan">{lives}</strong></p>
              <div className="lc-next-info">
                <span className="lc-arrow">▶</span>
                <span>LEVEL {levelNum + 1}: <strong>{getLevelConfig(levelNum + 1).name}</strong></span>
              </div>
              <button
                className="game-control-btn primary-btn font-display"
                style={{ marginTop: '14px', background: '#ffd060', color: '#000' }}
                onClick={() => advanceLevel(lives, score, levelNum + 1)}
              >
                NEXT LEVEL →
              </button>
            </div>
          </div>
        )}

        {!isPlaying && (
          <div className="game-overlay start-overlay">
            <div className="overlay-content">
              <Award size={24} className="text-cyan" style={{ marginBottom: '10px' }} />
              <h2 className="text-cyan font-display">THINK BEFORE CLICK</h2>
              <p className="subtitle">Drop square tool blocks from the swinging crane hook to stack them.</p>
              <button className="game-control-btn primary-btn font-display" onClick={startGame}>
                BOOT ENGINE
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="highscore-banner">
        <span>BEST SYSTEM RUN: </span>
        <strong className="text-cyan">{highScore}</strong>
      </div>
    </div>
  );
}
