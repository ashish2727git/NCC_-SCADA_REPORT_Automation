import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';

export default function SquadSyncArena(props) {
  const hoverLayer = useRef();

  const paperMat = new THREE.MeshStandardMaterial({
    color: '#e8dcca',
    roughness: 0.9,
    side: THREE.DoubleSide
  });

  const glowingBlue = new THREE.Color('#00bbff').multiplyScalar(1.5);

  useFrame((state) => {
    if (hoverLayer.current) {
      hoverLayer.current.position.y = Math.sin(state.clock.elapsedTime * 1.5) * 0.05 + 0.8;
      hoverLayer.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.2;
    }
  });

  return (
    <group {...props}>
      {/* Base Arena */}
      <mesh position={[0, 0.1, 0]} material={paperMat} castShadow receiveShadow>
        <cylinderGeometry args={[2, 1.5, 0.2, 12]} />
      </mesh>
      
      {/* Inner Ring (Scrim Marketplace) */}
      <mesh position={[0, 0.2, 0]} material={paperMat} castShadow>
        <cylinderGeometry args={[1, 1, 0.2, 12, 1, true]} />
      </mesh>

      {/* Floating Hierarchy Nodes */}
      <group ref={hoverLayer}>
        <mesh material={paperMat} castShadow position={[0, 0, 0]}>
          <octahedronGeometry args={[0.3]} />
        </mesh>
        
        {/* Connecting network lines */}
        {[[-1, -0.5, 0], [1, -0.5, 0], [0, -0.5, 1], [0, -0.5, -1]].map((pos, i) => (
          <group key={i}>
            <mesh position={pos} material={paperMat} castShadow>
              <boxGeometry args={[0.2, 0.2, 0.2]} />
            </mesh>
            <Line 
              points={[[0, 0, 0], pos]} 
              color={glowingBlue} 
              lineWidth={1} 
              transparent 
              opacity={0.6} 
            />
          </group>
        ))}
      </group>
    </group>
  );
}
