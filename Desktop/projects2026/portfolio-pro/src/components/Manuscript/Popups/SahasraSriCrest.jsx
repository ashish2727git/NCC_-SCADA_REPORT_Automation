import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function SahasraSriCrest(props) {
  const crestRef = useRef();

  const paperMat = new THREE.MeshStandardMaterial({
    color: '#e8dcca',
    roughness: 0.7,
    side: THREE.DoubleSide
  });

  const glowingGold = new THREE.Color('#ffcc00').multiplyScalar(1.5);
  const goldMat = new THREE.MeshStandardMaterial({
    color: glowingGold,
    emissive: glowingGold,
    emissiveIntensity: 0.3
  });

  useFrame((state) => {
    if (crestRef.current) {
      // Gentle levitation and rotation for the crest
      crestRef.current.position.y = Math.sin(state.clock.elapsedTime * 1.2) * 0.1 + 1.2;
      crestRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.8) * 0.3;
    }
  });

  return (
    <group {...props}>
      {/* Base Pedestal */}
      <mesh position={[0, 0.1, 0]} material={paperMat} castShadow receiveShadow>
        <cylinderGeometry args={[1, 1.2, 0.2, 6]} />
      </mesh>
      
      {/* Structural Pillars */}
      {[-0.6, 0.6].map((x, i) => (
        <mesh key={i} position={[x, 0.5, 0]} material={paperMat} castShadow>
          <cylinderGeometry args={[0.05, 0.05, 0.8, 8]} />
        </mesh>
      ))}

      {/* Floating Crest Shield */}
      <group ref={crestRef}>
        {/* Core Shield */}
        <mesh material={paperMat} castShadow rotation={[Math.PI / 2, 0, 0]}>
          <coneGeometry args={[0.8, 1.5, 3]} />
        </mesh>
        
        {/* Glowing Center Emblem */}
        <mesh material={goldMat} position={[0, 0, 0.2]} castShadow>
          <sphereGeometry args={[0.2, 16, 16]} />
        </mesh>
      </group>
    </group>
  );
}
