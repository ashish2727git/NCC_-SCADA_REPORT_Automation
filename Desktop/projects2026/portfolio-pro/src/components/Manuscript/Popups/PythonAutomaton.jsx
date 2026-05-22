import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function PythonAutomaton(props) {
  const gearsRef = useRef([]);

  const paperMat = new THREE.MeshStandardMaterial({
    color: '#e8dcca',
    roughness: 0.8,
    side: THREE.DoubleSide
  });

  const glowingGreen = new THREE.Color('#00ff66').multiplyScalar(1.2);
  const holoMat = new THREE.MeshStandardMaterial({
    color: glowingGreen,
    emissive: glowingGreen,
    emissiveIntensity: 0.5,
    transparent: true,
    opacity: 0.8,
    wireframe: true // Holographic style
  });

  useFrame((state) => {
    gearsRef.current.forEach((gear, i) => {
      if (gear) {
        // Alternate rotation direction based on index
        gear.rotation.z += (i % 2 === 0 ? 0.01 : -0.01) * (i + 1);
        
        // Slight hover for holographic gears
        if (i >= 2) {
           gear.position.y = Math.sin(state.clock.elapsedTime * 2 + i) * 0.05 + 1.0;
        }
      }
    });
  });

  const addGearRef = (el) => {
    if (el && !gearsRef.current.includes(el)) {
      gearsRef.current.push(el);
    }
  };

  return (
    <group {...props}>
      {/* Base Automaton Structure */}
      <mesh position={[0, 0.2, 0]} material={paperMat} castShadow receiveShadow>
        <boxGeometry args={[1.5, 0.4, 1.5]} />
      </mesh>
      
      {/* Physical Paper Gears */}
      <mesh ref={addGearRef} position={[-0.4, 0.45, 0]} rotation={[-Math.PI/2, 0, 0]} material={paperMat} castShadow>
        <cylinderGeometry args={[0.5, 0.5, 0.05, 12]} />
      </mesh>
      
      <mesh ref={addGearRef} position={[0.4, 0.45, 0]} rotation={[-Math.PI/2, 0, 0]} material={paperMat} castShadow>
        <cylinderGeometry args={[0.3, 0.3, 0.05, 12]} />
      </mesh>

      {/* Floating Holographic Gears */}
      <mesh ref={addGearRef} position={[0, 1.0, 0]} rotation={[-Math.PI/2 + 0.2, 0.2, 0]} material={holoMat} castShadow>
        <cylinderGeometry args={[0.6, 0.6, 0.1, 8]} />
      </mesh>
    </group>
  );
}
