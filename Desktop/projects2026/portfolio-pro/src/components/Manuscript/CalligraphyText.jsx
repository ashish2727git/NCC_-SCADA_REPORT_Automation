import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text } from '@react-three/drei';
import * as THREE from 'three';

export default function CalligraphyText({ 
  text, 
  revealProgress = 0, 
  pageTurnProgress = 0, 
  position = [0, 0, 0], 
  ...props 
}) {
  const customMaterial = useMemo(() => {
    // We use basic material because text doesn't explicitly need shadows on itself, 
    // it will cast/receive if we want, but we need high emissivity for the bloom glow.
    const mat = new THREE.MeshStandardMaterial({
      color: "#2a1508", // Dark brown ink final color
      emissive: "#ffaa00",
      emissiveIntensity: 0,
      transparent: true,
      side: THREE.DoubleSide
    });

    mat.onBeforeCompile = (shader) => {
      shader.uniforms.uPageTurn = { value: 0 };
      shader.uniforms.uReveal = { value: 0 };

      shader.vertexShader = shader.vertexShader.replace(
        '#include <common>',
        `
        #include <common>
        uniform float uPageTurn;
        varying float vLocalX;
        `
      ).replace(
        '#include <begin_vertex>',
        `
        #include <begin_vertex>
        
        vLocalX = position.x;
        
        // Exact same bending logic as the Page
        float spineDist = (position.x + 1.9); // Text must be placed relative to center just like Page
        float angle = uPageTurn * 3.14159; 
        float lift = sin(uPageTurn * 3.14159) * 2.0 * (spineDist / 3.8); 
        float cosA = cos(angle);
        float sinA = sin(angle);
        
        transformed.x = -1.9 + spineDist * cosA;
        transformed.y = position.y + sin(uPageTurn * 3.14159) * 0.5 * (spineDist / 3.8); 
        transformed.z = spineDist * sinA + lift;
        
        // Push slightly outwards along the normal to prevent z-fighting with the page
        transformed += normal * 0.01;
        `
      );

      // Fragment shader modifications for Reveal and Magic Ink Glow
      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <common>',
        `
        #include <common>
        uniform float uReveal;
        varying float vLocalX;
        `
      ).replace(
        '#include <dithering_fragment>',
        `
        #include <dithering_fragment>
        
        // We calculate bounds roughly from -1.5 to +1.5 locally (assuming centered text)
        // uReveal goes 0 to 1
        float revealX = mix(-2.0, 2.0, uReveal);
        
        // Mask out anything beyond revealX
        if (vLocalX > revealX) {
           discard;
        }
        
        // Calculate the leading edge for the glow
        float distanceToEdge = revealX - vLocalX;
        
        // Add a bright golden color at the very edge (glow)
        // It cools down very quickly over 0.2 units
        float glowIntensity = smoothstep(0.2, 0.0, distanceToEdge);
        
        vec3 finalColor = mix(gl_FragColor.rgb, vec3(1.0, 0.8, 0.1), glowIntensity);
        gl_FragColor = vec4(finalColor, gl_FragColor.a);
        `
      );
      
      mat.userData.shader = shader;
    };
    return mat;
  }, []);

  useFrame(() => {
    if (customMaterial.userData.shader) {
      customMaterial.userData.shader.uniforms.uPageTurn.value = pageTurnProgress;
      customMaterial.userData.shader.uniforms.uReveal.value = revealProgress;
    }
  });

  return (
    <Text 
      font="https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZJhjp-Ek-_EeA.woff"
      position={position}
      material={customMaterial}
      fontSize={0.2}
      maxWidth={3.0}
      lineHeight={1.5}
      {...props}
    >
      {text}
    </Text>
  );
}
