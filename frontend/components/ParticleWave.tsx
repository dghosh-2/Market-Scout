'use client';

import { useEffect, useRef } from 'react';

type ParticleWaveProps = {
  className?: string;
  density?: number;
};

export default function ParticleWave({ className = '', density = 14 }: ParticleWaveProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const { clientWidth, clientHeight } = canvas;
      canvas.width = clientWidth * dpr;
      canvas.height = clientHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const step = 420 / density;
    let t = 0;

    const draw = () => {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = '#ffffff';

      for (let x = 0; x < w + step; x += step) {
        for (let y = 0; y < h + step; y += step) {
          const nx = x / w - 0.5;
          const ny = y / h - 0.5;
          const wave =
            Math.sin(nx * 6 + t * 0.9) * Math.cos(ny * 5 + t * 0.7) * 0.35 +
            Math.sin(nx * 3 + ny * 4 + t * 0.5) * 0.2;
          const z = wave * 28;
          const alpha = 0.15 + (wave + 0.55) * 0.35;
          const r = 0.9 + (wave + 0.5) * 0.5;
          ctx.globalAlpha = Math.min(0.95, Math.max(0.08, alpha));
          ctx.beginPath();
          ctx.arc(x + z * nx, y + z * 0.4, r, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
      t += 0.016;
      frameRef.current = requestAnimationFrame(draw);
    };

    frameRef.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(frameRef.current);
      ro.disconnect();
    };
  }, [density]);

  return (
    <canvas
      ref={canvasRef}
      className={`pointer-events-none w-full h-full block ${className}`}
      aria-hidden
    />
  );
}
