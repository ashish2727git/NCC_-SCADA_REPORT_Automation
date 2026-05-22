import { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function SmoothSkewScroll({ children }) {
  const wrapperRef = useRef(null);
  const contentRef = useRef(null);

  useEffect(() => {
    // We will build a highly-optimized native GSAP ticker to calculate scroll velocity and apply a Y-axis skew.
    let currentY = window.pageYOffset;
    let targetY = currentY;
    let skew = 0;
    
    // We update body height to allow native scrolling
    document.body.style.height = `${contentRef.current.getBoundingClientRect().height}px`;

    const setY = gsap.quickSetter(contentRef.current, 'y', 'px');
    const setSkew = gsap.quickSetter(contentRef.current, 'skewY', 'deg');

    const updateScroll = () => {
      targetY = window.pageYOffset;
      // Interpolate smooth scroll
      currentY += (targetY - currentY) * 0.1;
      
      // Calculate velocity
      const velocity = targetY - currentY;
      skew = velocity * 0.05; // Skew multiplier
      
      // Clamp skew
      skew = Math.max(-10, Math.min(10, skew));

      setY(-currentY);
      setSkew(skew);
      
      requestAnimationFrame(updateScroll);
    };
    
    // Watch for resize to update height
    const resizeObserver = new ResizeObserver(() => {
      document.body.style.height = `${contentRef.current.getBoundingClientRect().height}px`;
    });
    resizeObserver.observe(contentRef.current);

    requestAnimationFrame(updateScroll);

    return () => {
      document.body.style.height = 'auto';
      resizeObserver.disconnect();
    };
  }, []);

  return (
    <div ref={wrapperRef} style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', overflow: 'hidden' }}>
      <div ref={contentRef} style={{ willChange: 'transform' }}>
        {children}
      </div>
    </div>
  );
}
