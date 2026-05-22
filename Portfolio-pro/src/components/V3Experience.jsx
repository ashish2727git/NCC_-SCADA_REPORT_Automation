import { useRef, useMemo, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { MeshTransmissionMaterial, Image } from '@react-three/drei';
import * as THREE from 'three';

// 1. Interactive Particle Storm
function ParticleStorm() {
  const count = 5000;
  const meshRef = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  
  // Base positions
  const basePositions = useMemo(() => {
    const pos = [];
    for (let i = 0; i < count; i++) {
      const r = 20 * Math.cbrt(Math.random());
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);
      
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi) - 10;
      pos.push(new THREE.Vector3(x, y, z));
    }
    return pos;
  }, []);

  useFrame((state, delta) => {
    if (!meshRef.current) return;
    
    // Convert normalized device coordinates (state.pointer) to a world vector
    const pointer = new THREE.Vector3(state.pointer.x * 10, state.pointer.y * 10, -5);
    
    basePositions.forEach((basePos, i) => {
      // Calculate distance to pointer
      let dist = basePos.distanceTo(pointer);
      let repulsion = new THREE.Vector3();
      
      if (dist < 4) {
        repulsion.subVectors(basePos, pointer).normalize().multiplyScalar((4 - dist) * 0.5);
      }
      
      // Floating animation
      const time = state.clock.elapsedTime;
      const floatX = Math.sin(time * 0.5 + i) * 0.5;
      const floatY = Math.cos(time * 0.6 + i) * 0.5;
      
      dummy.position.copy(basePos).add(repulsion).add(new THREE.Vector3(floatX, floatY, 0));
      
      // Scale pulse
      const scale = 1 + Math.sin(time * 2 + i) * 0.5;
      dummy.scale.setScalar(scale * 0.05);
      
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    });
    
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[null, null, count]}>
      <icosahedronGeometry args={[1, 0]} />
      <meshBasicMaterial color="#dfa52f" wireframe opacity={0.6} transparent />
    </instancedMesh>
  );
}

// 2. Heavy Glass Gallery Panels
function GlassPanel({ position, textureUrl, title }) {
  return (
    <group position={position}>
      {/* The refraction glass */}
      <mesh position={[0, 0, 0.5]}>
        <boxGeometry args={[4.2, 2.7, 0.2]} />
        <MeshTransmissionMaterial 
          thickness={1.5}
          roughness={0.1}
          transmission={1}
          ior={1.5}
          chromaticAberration={0.06}
          backside
        />
      </mesh>
      
      {/* The actual image embedded inside the glass */}
      <Image url={textureUrl} scale={[4, 2.5]} position={[0, 0, 0]} />
    </group>
  );
}

export default function V3Experience() {
  const { camera } = useThree();
  const targetZ = useRef(5);

  useEffect(() => {
    // 3. Raw Native Hardware Scroll Interceptor (Bypassing DOM overlays completely)
    const handleWheel = (e) => {
      // Dollying the camera target Z based on hardware wheel delta
      targetZ.current += e.deltaY * 0.01;
      
      // Clamp the flight path between Z=5 (start) and Z=-30 (end)
      if (targetZ.current > 5) targetZ.current = 5;
      if (targetZ.current < -30) targetZ.current = -30;
    };
    
    window.addEventListener('wheel', handleWheel, { passive: true });
    return () => window.removeEventListener('wheel', handleWheel);
  }, []);

  useFrame(() => {
    // Smooth camera interpolation towards the targetZ
    camera.position.z += (targetZ.current - camera.position.z) * 0.05;
  });

  return (
    <>
      <ParticleStorm />
      
      <GlassPanel position={[-2, 0, -5]} textureUrl="/img1.jpg" />
      <GlassPanel position={[2, -1, -15]} textureUrl="/img2.jpg" />
      <GlassPanel position={[-1.5, 1, -25]} textureUrl="/img3.jpg" />
    </>
  );
}
