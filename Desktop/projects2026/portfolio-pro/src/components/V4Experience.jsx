import { useState, useRef, useEffect } from 'react';
import MagneticNode from './MagneticNode';
import './V4Experience.css';
import gsap from 'gsap';

function ImageTrail() {
  const images = ['/img1.jpg', '/img2.jpg', '/img3.jpg'];
  const trailRef = useRef([]);

  useEffect(() => {
    let zIndexCounter = 1;
    let lastX = 0;
    let lastY = 0;
    let activeIndex = 0;

    const handleMouseMove = (e) => {
      const distance = Math.hypot(e.clientX - lastX, e.clientY - lastY);
      
      // Spawn image every 100px of movement
      if (distance > 100) {
        lastX = e.clientX;
        lastY = e.clientY;
        
        const currentRef = trailRef.current[activeIndex];
        if (currentRef) {
           // Instantly position
           gsap.set(currentRef, { 
             x: e.clientX, 
             y: e.clientY,
             xPercent: -50,
             yPercent: -50,
             opacity: 1,
             scale: 1,
             zIndex: zIndexCounter++
           });
           
           // Fade out automatically
           gsap.to(currentRef, {
             opacity: 0,
             scale: 0.5,
             duration: 1.5,
             ease: "power2.out",
             delay: 0.2
           });
        }
        activeIndex = (activeIndex + 1) % images.length;
      }
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="image-trail-container">
      {images.map((src, i) => (
        <img 
          key={i}
          ref={el => trailRef.current[i] = el}
          src={src} 
          className="trail-image"
          alt=""
        />
      ))}
    </div>
  );
}

export default function V4Experience() {
  return (
    <div className="v4-container">
      <ImageTrail />
      
      <section className="v4-hero">
        <div className="v4-header">
          <MagneticNode>
            <a href="#" className="v4-logo">STUDIO.AI</a>
          </MagneticNode>
          <MagneticNode>
            <a href="#" className="v4-contact">Let's Talk</a>
          </MagneticNode>
        </div>

        <div className="v4-hero-text-container">
          <h1 className="v4-massive-text">
            <span>WE DISRUPT</span>
            <span>ORDINARY.</span>
          </h1>
          <p className="v4-sub-text">
            Building the next generation of creative digital experiences using hyper-advanced DOM manipulation and raw WebGL power.
          </p>
        </div>
      </section>

      <section className="v4-manifesto">
        <div className="manifesto-grid">
          <h2>THE AWWWARDS AESTHETIC</h2>
          <p className="large-p">
            We don't build generic websites. We build <strong>kinetic architecture</strong>. 
            By fusing brutally minimalist design with liquid scroll physics, your brand transcends the screen.
          </p>
        </div>
      </section>
      
      <section className="v4-gallery-teaser">
        <h1>[ SCROLL FURTHER FOR THE GALLERY ]</h1>
        <div className="teaser-images">
             <img src="/img1.jpg" alt="" className="v4-large-img" />
             <img src="/img2.jpg" alt="" className="v4-large-img" />
        </div>
      </section>
      
      <section className="v4-footer">
        <h1 className="v4-massive-text">READY?</h1>
      </section>
    </div>
  );
}
