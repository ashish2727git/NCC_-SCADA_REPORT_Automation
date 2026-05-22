import React, { Suspense, useState, useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, Effects } from '@react-three/drei';
import { EffectComposer, Bloom, Noise } from '@react-three/postprocessing';
import AncientBook from './AncientBook';
import './Manuscript.css'; // Add some basic CSS to reset canvas to fullscreen

export default function ManuscriptExperience() {
  const [entered, setEntered] = useState(false);
  const audioRef = useRef();

  const handleEnter = () => {
    setEntered(true);
    if (audioRef.current) {
      audioRef.current.volume = 0.5;
      audioRef.current.play().catch(e => console.warn("Audio play failed:", e));
    }
  };

  return (
    <>
    {/* Audio Element: Wind/Chimes */}
    <audio 
      ref={audioRef} 
      src="https://actions.google.com/sounds/v1/water/waves_crashing_on_rock_beach.ogg" // placeholder 
      loop 
    />

    {!entered && (
      <div className="manuscript-enter-screen" onClick={handleEnter} style={{
        position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', 
        backgroundColor: '#050505', display: 'flex', flexDirection: 'column',
        justifyContent: 'center', alignItems: 'center', zIndex: 1000, color: '#f4e0c3',
        fontFamily: 'serif', cursor: 'pointer'
      }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '20px', letterSpacing: '4px' }}>TALA PATRA</h1>
        <p style={{ opacity: 0.7, letterSpacing: '2px' }}>[ CLICK TO ENTER THE VOID ]</p>
      </div>
    )}

    <div className="manuscript-container" style={{ position: 'fixed', opacity: entered ? 1 : 0, transition: 'opacity 2s ease-in-out' }}>
      <Canvas
        camera={{ position: [0, 5, 10], fov: 45 }}
        gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
        dpr={[1, 2]}
      >
        <color attach="background" args={['#050505']} />
        
        <ambientLight intensity={0.1} color="#ffffff" />
        {/* Animated flickering candle light */}
        <pointLight 
          position={[-5, 5, 5]} 
          intensity={1.5} 
          color="#ffaa00" 
          distance={20} 
          castShadow 
          shadow-mapSize={[1024, 1024]}
        />

        <Suspense fallback={null}>
          <AncientBook />
        </Suspense>

        <EffectComposer disableNormalPass>
          <Bloom luminanceThreshold={0.5} luminanceSmoothing={0.9} intensity={2.0} mipmapBlur />
          <Noise opacity={0.05} />
        </EffectComposer>

        <OrbitControls enableZoom={true} enablePan={true} maxPolarAngle={Math.PI / 2} enableDamping />
      </Canvas>
    </div>
    
    {/* Scroll container that GSAP ScrollTrigger will bind to */}
    <div className="manuscript-scroll-area" style={{ position: 'relative', width: '100%', height: '500vh', zIndex: 1, pointerEvents: 'none' }}></div>
    
    {/* Ambient Ocean/Wind Audio could go here (invisible) */}
    </>
  );
}
