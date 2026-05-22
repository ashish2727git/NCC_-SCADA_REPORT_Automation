import { useRef, useMemo, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

const vertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const fragmentShader = `
  uniform float uTime;
  uniform vec2 uResolution;
  uniform float uScrollVelocity;
  
  varying vec2 vUv;

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution.xy;
    
    // Soothing slow time factor
    float t = uTime * 0.15;
    
    // Create a subtle dual-color ambient mesh
    // Dark deep slate charcoal (#0a0d14) blended with a soft deep navy (#0c101c)
    vec3 baseBg = vec3(0.04, 0.05, 0.08); 
    
    // Add soft floating light leaks (one cyan, one purple-indigo)
    vec2 light1Pos = vec2(
      0.5 + sin(t * 0.8) * 0.3,
      0.5 + cos(t * 0.6) * 0.3
    );
    vec2 light2Pos = vec2(
      0.5 + cos(t * 0.5) * 0.4,
      0.5 + sin(t * 0.7) * 0.2
    );
    
    float dist1 = length(uv - light1Pos);
    float dist2 = length(uv - light2Pos);
    
    // Soft, wide radial fallout for ambient lights
    float light1 = smoothstep(0.8, 0.0, dist1) * 0.07;
    float light2 = smoothstep(0.7, 0.0, dist2) * 0.05;
    
    // Colors of the lights: Soft teal/cyan and soft muted indigo
    vec3 light1Color = vec3(0.0, 0.8, 0.9) * light1;
    vec3 light2Color = vec3(0.5, 0.2, 0.9) * light2;
    
    vec3 finalColor = baseBg + light1Color + light2Color;
    
    // Subtle grid lines overlay (very faint, for blueprint engineering look)
    vec2 grid = abs(fract(uv * 30.0 - 0.5) - 0.5) / fwidth(uv * 30.0);
    float gridLine = min(grid.x, grid.y);
    float gridIntensity = (1.0 - min(gridLine, 1.0)) * 0.015;
    
    finalColor += vec3(0.0, 0.8, 1.0) * gridIntensity;

    gl_FragColor = vec4(finalColor, 1.0);
  }
`;

export default function LiquidBackground() {
  const materialRef = useRef();
  const { size } = useThree();

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uResolution: { value: new THREE.Vector2(size.width, size.height) },
    uScrollVelocity: { value: 0 }
  }), [size.width, size.height]);

  useEffect(() => {
    let lastY = window.scrollY;
    let velocity = 0;
    
    const handleScroll = () => {
      const currentY = window.scrollY;
      velocity = Math.abs(currentY - lastY);
      lastY = currentY;
      
      if (materialRef.current) {
        materialRef.current.uniforms.uScrollVelocity.value += velocity * 0.1;
      }
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      // Decay velocity slowly
      materialRef.current.uniforms.uScrollVelocity.value *= 0.95;
    }
  });

  return (
    <mesh position={[0, 0, -1]}>
      <planeGeometry args={[100, 100]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        depthWrite={false}
      />
    </mesh>
  );
}
