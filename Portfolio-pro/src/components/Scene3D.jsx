import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, PointMaterial, Points } from '@react-three/drei';
import * as random from 'maath/random/dist/maath-random.esm';

function ParticleField(props) {
  const ref = useRef();
  
  // Create a sphere of particles
  const sphere = useMemo(() => {
    // Generate random points in a sphere with radius 1.5
    const positions = random.inSphere(new Float32Array(5000), { radius: 1.5 });
    // Handle NaN values which maath sometimes produces if not careful (fallback to 0)
    for(let i = 0; i < positions.length; i++) {
        if(isNaN(positions[i])) positions[i] = 0;
    }
    return positions;
  }, []);

  useFrame((state, delta) => {
    // Slowly rotate the particle field
    ref.current.rotation.x -= delta / 10;
    ref.current.rotation.y -= delta / 15;
    
    // Add subtle mouse-based movement
    const pointerX = state.pointer.x;
    const pointerY = state.pointer.y;
    ref.current.position.x += (pointerX * 0.2 - ref.current.position.x) * 0.1;
    ref.current.position.y += (pointerY * 0.2 - ref.current.position.y) * 0.1;
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere} stride={3} frustumCulled={false} {...props}>
        <PointMaterial
          transparent
          color="#00f0ff"
          size={0.004}
          sizeAttenuation={true}
          depthWrite={false}
        />
      </Points>
    </group>
  );
}

function FloatingShapes() {
    return (
        <Float speed={2} rotationIntensity={1.5} floatIntensity={2} floatingRange={[-0.1, 0.1]}>
            <mesh position={[1, 1, 0]} rotation={[0.5, 0.5, 0]}>
                <torusKnotGeometry args={[0.3, 0.1, 100, 16]} />
                <meshStandardMaterial color="#8a2be2" wireframe />
            </mesh>
            <mesh position={[-1, -1, 0]} rotation={[-0.5, -0.5, 0]}>
                <icosahedronGeometry args={[0.4, 0]} />
                <meshStandardMaterial color="#ff0055" wireframe />
            </mesh>
        </Float>
    );
}

export default function Scene3D() {
  return (
    <div className="scene-container">
      <Canvas camera={{ position: [0, 0, 2] }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <ParticleField />
        <FloatingShapes />
      </Canvas>
    </div>
  );
}
