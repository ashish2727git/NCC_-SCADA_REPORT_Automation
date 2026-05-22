import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function Page({ index, progress = 0.5, children, ...props }) {
  const meshRef = useRef();
  
  // Custom material handling to add bending/peeling
  const customMaterial = useMemo(() => {
    const mat = new THREE.MeshStandardMaterial({
      color: "#f4e0c3", 
      roughness: 0.8,
      side: THREE.DoubleSide
    });

    mat.onBeforeCompile = (shader) => {
      shader.uniforms.uProgress = { value: 0 };
      
      shader.vertexShader = shader.vertexShader.replace(
        '#include <common>',
        `
        #include <common>
        uniform float uProgress;
        `
      ).replace(
        '#include <begin_vertex>',
        `
        #include <begin_vertex>
        
        // Bending logic: 
        // uProgress goes from 0 (right page) to 1 (left page)
        // At 0.5, the page is floating in the middle
        
        float turn = uProgress; // 0 to 1
        
        // Base X position of the vertex
        float x = position.x;
        
        // Bend factor based on distance from spine (assuming spine is at x = 0)
        // The right edge is at x = 3.8
        
        float spineDist = (x + 1.9); // assuming centered geometry size 3.8, so spine is at -1.9 relative to center
        
        // Bending math
        float angle = turn * 3.14159; 
        
        // Z lift: it peels up more towards the center of the turn
        float lift = sin(turn * 3.14159) * 2.0 * (spineDist / 3.8); 
        
        // Apply rotation around the spine
        float cosA = cos(angle);
        float sinA = sin(angle);
        
        transformed.x = -1.9 + spineDist * cosA;
        transformed.y = position.y + sin(turn * 3.14159) * 0.5 * (spineDist / 3.8); // slight twist
        transformed.z = spineDist * sinA + lift;
        `
      );
      
      mat.userData.shader = shader;
    };
    return mat;
  }, []);

  useFrame(() => {
    if (customMaterial.userData.shader) {
      customMaterial.userData.shader.uniforms.uProgress.value = progress;
    }
  });

  return (
    <group {...props} position={[1.9, 0, 0]}>
      {/* 
        Position offsets it so the spine is at 0 in the parent space.
        Geometry width is 3.8, so center is 1.9 
      */}
      <mesh ref={meshRef} receiveShadow castShadow material={customMaterial}>
        <planeGeometry args={[3.8, 4.8, 32, 32]} />
      </mesh>
      
      {/* Content wrapper - we need to position the text slightly above the page */}
      {/* Wait, the text won't bend if it's placed as a normal child. 
          For text to bend WITH the page, it has to be mapped to the material,
          or we do a custom shader on the text as well. 
          Because drawing text to a canvas texture and mapping it is standard, 
          let's plan on using CalligraphyText via a separate plane placed slightly above 
          and employing the exact same vertex shader logic! */}
    </group>
  );
}
