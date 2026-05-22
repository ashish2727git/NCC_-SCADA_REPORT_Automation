import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';

export default function CloudInfrastructure({ pageTurnProgress = 0, ...props }) {
  const groupRef = useRef();
  const orbitingNodes = useRef();

  // Paper material
  const paperMat = new THREE.MeshStandardMaterial({
    color: '#e8dcca',
    roughness: 0.9,
    side: THREE.DoubleSide
  });
  
  // Glowing thread material
  const threadColor = new THREE.Color('#ffaa00').multiplyScalar(2);

  useFrame((state) => {
    if (orbitingNodes.current) {
      // Rotate the detached nodes slowly
      orbitingNodes.current.rotation.y += 0.005;
      
      // Floating effect
      orbitingNodes.current.position.y = Math.sin(state.clock.elapsedTime) * 0.1 + 0.5;
    }
    
    // Popup scaling/folding based on page turn progress
    // Ideally it pops up from 0 to 1 as the page lands
    if (groupRef.current) {
      // simplified fold animation based on page progress for now
      // assume 0 = closed left, 1 = open flat, 2 = closed right
      // This logic will be fleshed out with GSAP, for now static scale
    }
  });

  return (
    <group ref={groupRef} {...props}>
      {/* Central Base (EKS Cluster Map) */}
      <mesh position={[0, 0.05, 0]} material={paperMat} castShadow receiveShadow rotation={[-Math.PI/2, 0, 0]}>
        <cylinderGeometry args={[1.5, 1.5, 0.05, 6]} />
      </mesh>

      {/* Detached Orbiting Nodes */}
      <group ref={orbitingNodes} position={[0, 0.5, 0]}>
        {[0, 1, 2].map((i) => {
          const angle = (i / 3) * Math.PI * 2;
          const x = Math.cos(angle) * 1.8;
          const z = Math.sin(angle) * 1.8;
          return (
            <group key={i} position={[x, 0, z]}>
              <mesh material={paperMat} castShadow>
                <boxGeometry args={[0.4, 0.4, 0.4]} />
              </mesh>
              {/* Magical Thread connecting back to center base */}
              <Line 
                points={[[0, 0, 0], [-x, -0.5, -z]]} 
                color={threadColor} 
                lineWidth={1} 
                transparent 
                opacity={0.5} 
              />
            </group>
          );
        })}
      </group>
      
      {/* Jenkins Pipeline representation */}
      <mesh position={[0, 0.3, 0]} material={paperMat} castShadow>
        <boxGeometry args={[1.2, 0.2, 0.6]} />
      </mesh>
    </group>
  );
}
