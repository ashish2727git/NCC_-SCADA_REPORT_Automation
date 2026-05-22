import React, { useRef, useLayoutEffect, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import Page from './Page';
import CalligraphyText from './CalligraphyText';
import CloudInfrastructure from './Popups/CloudInfrastructure';
import SquadSyncArena from './Popups/SquadSyncArena';
import PythonAutomaton from './Popups/PythonAutomaton';
import SahasraSriCrest from './Popups/SahasraSriCrest';

gsap.registerPlugin(ScrollTrigger);

export default function AncientBook(props) {
  const groupRef = useRef();
  const pagesData = useRef([
    { id: 0, progress: 0, textProgress: 0 },
    { id: 1, progress: 0, textProgress: 0 },
    { id: 2, progress: 0, textProgress: 0 },
    { id: 3, progress: 0, textProgress: 0 },
  ]);

  const [renderState, setRenderState] = useState(0); // Force re-render if needed, though useFrame is better

  // Use GSAP inside useLayoutEffect to bind to the empty scroll container
  useLayoutEffect(() => {
    // Setup a GSAP timeline tied to scroll
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: ".manuscript-scroll-area",
        start: "top top",
        end: "bottom bottom",
        scrub: 0.5,
      }
    });

    // Sequence the animations:
    // Page 0 turn -> Page 0 Text -> Page 1 turn -> Page 1 text, etc.
    pagesData.current.forEach((page, i) => {
      // 1. Turn the page (0 to 1)
      tl.to(page, {
        progress: 1.0,
        duration: 1,
        ease: "power2.inOut",
        onUpdate: () => setRenderState(Math.random()) // rough sync for react to pass down the uniform, ideally use a store or ref
      }, `seq${i}`);

      // 2. Reveal the ink (0 to 1)
      tl.to(page, {
        textProgress: 1.0,
        duration: 1.5,
        ease: "none",
        onUpdate: () => setRenderState(Math.random())
      }, `seq${i}+=0.5`); // Overlap text reveal slightly with the end of the turn
    });

    return () => {
      tl.kill();
      ScrollTrigger.getAll().forEach(t => t.kill());
    };
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      const t = state.clock.getElapsedTime();
      groupRef.current.position.y = Math.sin(t * 0.5) * 0.2;
      groupRef.current.rotation.x = Math.sin(t * 0.3) * 0.05;
      groupRef.current.rotation.y = Math.sin(t * 0.2) * 0.05;
      groupRef.current.rotation.z = Math.sin(t * 0.4) * 0.02;
    }
  });

  return (
    <group ref={groupRef} {...props}>
      {/* Book Base */}
      <mesh position={[0, -0.1, 0]} receiveShadow castShadow>
        <boxGeometry args={[8, 0.2, 5]} />
        <meshStandardMaterial color="#2c1a10" roughness={0.9} />
      </mesh>
      
      {/* Right Pages Stack */}
      <mesh position={[1.9, -0.05, 0]} receiveShadow castShadow>
        <boxGeometry args={[3.8, 0.1, 4.8]} />
        <meshStandardMaterial color="#d4b483" roughness={0.8} />
      </mesh>
      
      {/* Left Pages Stack */}
      <mesh position={[-1.9, -0.05, 0]} receiveShadow castShadow>
        <boxGeometry args={[3.8, 0.1, 4.8]} />
        <meshStandardMaterial color="#d4b483" roughness={0.8} />
      </mesh>

      {/* Pages & Popups */}
      
      {/* PAGE 0: Cloud Infrastructure */}
      {/* Z-offsets to prevent z-fighting */}
      <Page index={0} progress={pagesData.current[0].progress} position={[0, 0.01, 0]}>
         {/* We can't put Calligraphy inside Page as children easily due to the way we built Page,
             we render it on top but using the same progress */}
      </Page>
      <CalligraphyText 
        text="Chapter I: Cloud Computing\nThe foundation of our temple." 
        revealProgress={pagesData.current[0].textProgress} 
        pageTurnProgress={pagesData.current[0].progress} 
        position={[-1.0, 0.05, 0]} 
      />
      {/* Render popup only when page is turning/turned */}
      <group position={[-1.9, 0.1, 0]} scale={pagesData.current[0].progress}>
        <CloudInfrastructure />
      </group>

      {/* PAGE 1: SquadSync Arena */}
      <Page index={1} progress={pagesData.current[1].progress} position={[0, 0.02, 0]} />
      <CalligraphyText 
        text="Chapter II: SquadSync Arena\nA colosseum for the modern era." 
        revealProgress={pagesData.current[1].textProgress} 
        pageTurnProgress={pagesData.current[1].progress} 
        position={[-1.0, 0.06, 0]} 
      />
      <group position={[-1.9, 0.1, 0]} scale={pagesData.current[1].progress}>
        <SquadSyncArena />
      </group>

      {/* PAGE 2: Python Automaton */}
      <Page index={2} progress={pagesData.current[2].progress} position={[0, 0.03, 0]} />
      <CalligraphyText 
        text="Chapter III: Automation Machine\nThe gears that never sleep." 
        revealProgress={pagesData.current[2].textProgress} 
        pageTurnProgress={pagesData.current[2].progress} 
        position={[-1.0, 0.07, 0]} 
      />
      <group position={[-1.9, 0.1, 0]} scale={pagesData.current[2].progress}>
        <PythonAutomaton />
      </group>
      
      {/* PAGE 3: Sahasra Sri Crest */}
      <Page index={3} progress={pagesData.current[3].progress} position={[0, 0.04, 0]} />
      <CalligraphyText 
        text="Chapter IV: Sahasra Sri\nThe crest of ultimate truth." 
        revealProgress={pagesData.current[3].textProgress} 
        pageTurnProgress={pagesData.current[3].progress} 
        position={[-1.0, 0.08, 0]} 
      />
      <group position={[-1.9, 0.1, 0]} scale={pagesData.current[3].progress}>
        <SahasraSriCrest />
      </group>

    </group>
  );
}
