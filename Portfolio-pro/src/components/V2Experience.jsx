import { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useScroll } from '@react-three/drei';
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
  uniform float uScroll;
  
  varying vec2 vUv;
  
  // High-performance simplex noise
  vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }
  
  float snoise(vec2 v) {
    const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
    vec2 i  = floor(v + dot(v, C.yy) );
    vec2 x0 = v -   i + dot(i, C.xx);
    vec2 i1;
    i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    i = mod289(i);
    vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 )) + i.x + vec3(0.0, i1.x, 1.0 ));
    vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
    m = m*m;
    m = m*m;
    vec3 x = 2.0 * fract(p * C.www) - 1.0;
    vec3 h = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;
    m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
    vec3 g;
    g.x  = a0.x  * x0.x  + h.x  * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
  }

  void main() {
    vec2 st = gl_FragCoord.xy/uResolution.xy;
    st.x *= uResolution.x/uResolution.y;

    // Create a tunneling grid effect based on scroll
    vec2 pos = vec2(st*5.0);
    float n = snoise(pos + uTime * 0.1 + uScroll * 10.0);
    
    // Distort coordinates for laser grid
    vec2 gridPos = fract(pos + n * 0.5);
    float lines = smoothstep(0.0, 0.05, gridPos.x) * smoothstep(0.0, 0.05, gridPos.y);
    
    // Core cyber color scheme
    vec3 color1 = vec3(0.0, 0.94, 1.0); // Cyan
    vec3 color2 = vec3(0.54, 0.17, 0.89); // Purple
    
    vec3 finalColor = mix(color1, color2, n * 0.5 + 0.5) * (1.0 - lines);
    
    // Add pulsing glow based on scroll
    finalColor += color1 * (sin(uTime * 2.0 + uScroll * 20.0) * 0.2);

    // Fade to black at edges
    float vignette = length(vUv - 0.5);
    finalColor *= smoothstep(0.8, 0.2, vignette);

    // Extreme bloom values
    if (finalColor.r > 0.1 || finalColor.g > 0.1) {
       finalColor *= 2.0; // Overexpose to trigger bloom
    }

    gl_FragColor = vec4(finalColor, 1.0);
  }
`;

function BackgroundShader() {
  const materialRef = useRef();
  const { size } = useThree();
  const scroll = useScroll();

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uResolution: { value: new THREE.Vector2(size.width, size.height) },
    uScroll: { value: 0 },
  }), [size.width, size.height]);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      // scroll.offset goes 0 -> 1 over the duration of the scroll
      materialRef.current.uniforms.uScroll.value = scroll.offset;
    }
  });

  return (
    <mesh position={[0, 0, -10]}>
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

function ProjectGallery() {
  const scroll = useScroll();
  const groupRef = useRef();

  useFrame(() => {
    // Move the entire gallery towards the camera based on scroll
    // Scroll 0 -> 1 moves group Z from -20 to +10 (flying through)
    const zPos = -20 + (scroll.offset * 30);
    groupRef.current.position.z = zPos;
  });

  return (
    <group ref={groupRef}>
      {/* Project 1 */}
      <group position={[-2, 0, -5]}>
        <mesh>
          <planeGeometry args={[4, 2.5]} />
          <meshBasicMaterial color="#00f0ff" wireframe={true} transparent opacity={0.8} />
        </mesh>
      </group>
      
      {/* Project 2 */}
      <group position={[2, -1, -12]}>
        <mesh>
          <planeGeometry args={[4, 2.5]} />
          <meshBasicMaterial color="#8a2be2" wireframe={true} transparent opacity={0.8} />
        </mesh>
      </group>

      {/* Project 3 */}
      <group position={[-1.5, 1, -19]}>
        <mesh>
          <planeGeometry args={[4, 2.5]} />
          <meshBasicMaterial color="#ff0055" wireframe={true} transparent opacity={0.8} />
        </mesh>
      </group>
    </group>
  );
}

export default function V2Experience() {
  return (
    <>
      <BackgroundShader />
      <ProjectGallery />
    </>
  );
}
