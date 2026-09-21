import React, { useEffect, useRef } from 'react';

interface StageRouteMapProps {
  progress: number;
  onExplore: () => void;
}

interface Point {
  x: number;
  y: number;
}

export const StageRouteMap: React.FC<StageRouteMapProps> = ({ progress, onExplore }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const pClamped = Math.max(0, Math.min(1, progress));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let startTime = performance.now();

    const render = (now: number) => {
      const dpr = window.devicePixelRatio || 1;
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;

      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height * 0.44;
      const maxRadius = Math.min(width, height) * 0.38;

      // 1. Generate 26 points on a phyllotaxis spiral
      // angle: i * 2.399, radius: sqrt(i / 26) * maxRadius
      const totalPoints = 26;
      const points: Point[] = [];
      for (let i = 0; i < totalPoints; i++) {
        const theta = i * 2.399;
        const r = Math.sqrt(i / (totalPoints - 1)) * maxRadius;
        const x = centerX + r * Math.cos(theta);
        const y = centerY + r * Math.sin(theta);
        points.push({ x, y });
      }

      // 2. Connect every pair closer than threshold with 1px ink hairlines
      const connectThreshold = maxRadius * 0.48;
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(17, 16, 16, 0.16)';

      for (let i = 0; i < totalPoints; i++) {
        for (let j = i + 1; j < totalPoints; j++) {
          const dx = points[i].x - points[j].x;
          const dy = points[i].y - points[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < connectThreshold) {
            ctx.beginPath();
            ctx.moveTo(points[i].x, points[i].y);
            ctx.lineTo(points[j].x, points[j].y);
            ctx.stroke();
          }
        }
      }

      // 3. Draw dots for all 26 lattice nodes
      for (let i = 0; i < totalPoints; i++) {
        ctx.fillStyle = '#111010';
        ctx.beginPath();
        ctx.arc(points[i].x, points[i].y, 3, 0, Math.PI * 2);
        ctx.fill();

        // Small mono index label for architectural aesthetics
        ctx.fillStyle = 'rgba(17, 16, 16, 0.4)';
        ctx.font = '9px "JetBrains Mono", monospace';
        ctx.fillText(`N${String(i).padStart(2, '0')}`, points[i].x + 5, points[i].y - 5);
      }

      // 4. Trace ONE specific route through a deterministic sequence
      const routeIndices = [0, 3, 7, 12, 17, 21, 25];
      const routePoints = routeIndices.map((idx) => points[idx]);

      // Calculate total route path length
      const segmentLengths: number[] = [];
      let totalRouteLength = 0;
      for (let k = 0; k < routePoints.length - 1; k++) {
        const dx = routePoints[k + 1].x - routePoints[k].x;
        const dy = routePoints[k + 1].y - routePoints[k].y;
        const len = Math.sqrt(dx * dx + dy * dy);
        segmentLengths.push(len);
        totalRouteLength += len;
      }

      // Trace route as far as scroll progress has travelled
      const targetTravelDist = pClamped * totalRouteLength;
      let accumulatedDist = 0;
      let headPoint: Point = routePoints[0];

      ctx.lineWidth = 2.6;
      ctx.strokeStyle = '#DC201E';
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();
      ctx.moveTo(routePoints[0].x, routePoints[0].y);

      for (let k = 0; k < segmentLengths.length; k++) {
        const segLen = segmentLengths[k];
        const pStart = routePoints[k];
        const pEnd = routePoints[k + 1];

        if (accumulatedDist + segLen <= targetTravelDist) {
          // Entire segment is covered
          ctx.lineTo(pEnd.x, pEnd.y);
          accumulatedDist += segLen;
          headPoint = pEnd;
        } else if (accumulatedDist < targetTravelDist) {
          // Partial segment interpolation
          const remaining = targetTravelDist - accumulatedDist;
          const frac = remaining / segLen;
          const interpX = pStart.x + (pEnd.x - pStart.x) * frac;
          const interpY = pStart.y + (pEnd.y - pStart.y) * frac;
          ctx.lineTo(interpX, interpY);
          headPoint = { x: interpX, y: interpY };
          accumulatedDist = targetTravelDist;
          break;
        } else {
          break;
        }
      }
      ctx.stroke();

      // Highlight visited route nodes in red
      for (let k = 0; k < routeIndices.length; k++) {
        const pNode = routePoints[k];
        // If head has passed this node or is at it
        const dx = headPoint.x - pNode.x;
        const dy = headPoint.y - pNode.y;
        const distToHead = Math.sqrt(dx * dx + dy * dy);
        
        ctx.fillStyle = '#DC201E';
        ctx.beginPath();
        ctx.arc(pNode.x, pNode.y, 4, 0, Math.PI * 2);
        ctx.fill();
      }

      // 5. Draw pulsing dot and halo at the route head
      const elapsed = (now - startTime) / 1000;
      const pulseCycle = (elapsed * 2.5) % 1; // 0 to 1
      const haloRadius = 6 + pulseCycle * 14;
      const haloOpacity = Math.max(0, 1 - pulseCycle);

      // Halo ring
      ctx.beginPath();
      ctx.arc(headPoint.x, headPoint.y, haloRadius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(220, 32, 30, ${haloOpacity * 0.7})`;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Core head dot
      ctx.fillStyle = '#DC201E';
      ctx.beginPath();
      ctx.arc(headPoint.x, headPoint.y, 5, 0, Math.PI * 2);
      ctx.fill();

      // Outer head ring
      ctx.strokeStyle = '#111010';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(headPoint.x, headPoint.y, 7, 0, Math.PI * 2);
      ctx.stroke();

      ctx.restore();

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [pClamped]);

  return (
    <div className="relative sticky top-0 h-[100svh] w-full overflow-hidden bg-[#F8F3EC] text-[#111010] flex flex-col justify-between p-6 md:p-12 select-none">
      {/* 44px Ruled Background Grid */}
      <div className="absolute inset-0 poster-grid-44 pointer-events-none z-0" />

      {/* Top Header Furniture Line */}
      <div className="relative z-10 w-full flex items-center justify-between border-b-2 border-[#111010] pb-4 font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880] bg-[#F8F3EC]/80 backdrop-blur-xs">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 bg-[#DC201E]" />
          <span className="text-[#111010]">STAGE 04 // 26-NODE PHYLLOTAXIS ROUTING LATTICE</span>
        </div>
        <div className="text-[#111010]">
          SCROLL ROUTE PROGRESS: <span className="text-[#DC201E] font-bold">{Math.round(pClamped * 100)}%</span>
        </div>
      </div>

      {/* Center Canvas with mix-blend-mode: multiply */}
      <div className="relative z-10 w-full flex-1 flex items-center justify-center pointer-events-none">
        <canvas
          ref={canvasRef}
          className="w-full h-full max-w-4xl max-h-[60vh]"
          style={{ mixBlendMode: 'multiply' }}
        />
      </div>

      {/* Bottom Content Block (Bottom-aligned with Swiss closing line) */}
      <div className="relative z-10 w-full max-w-7xl mx-auto border-t-2 border-[#111010] pt-6 flex flex-col md:flex-row md:items-end justify-between gap-6 bg-[#F8F3EC]/90 backdrop-blur-xs">
        <div className="max-w-2xl">
          <div className="font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880] mb-2">
            // AUTONOMOUS TOPOLOGY ISOLATION
          </div>
          <h3 className="font-anton uppercase tracking-[-0.012em] text-2xl sm:text-3xl md:text-4xl text-[#111010] leading-[0.92] m-0">
            ADAPTIVE TRAFFIC IS <span className="text-[#DC201E]">DETERMINISTICALLY ROUTED</span> AROUND CIRCUIT FAILURES
          </h3>
          <p className="font-archivo text-[14px] md:text-[15px] leading-[1.6] text-[#111010]/80 mt-2 m-0">
            When upstream surges or downstream payment processors experience degradation, Rheos dynamically diverts load across non-congested node partitions with zero packet drop.
          </p>
        </div>

        <div className="flex flex-col items-start md:items-end gap-3 shrink-0">
          <button
            onClick={onExplore}
            className="group relative inline-flex items-center gap-3 px-6 py-3.5 bg-[#111010] hover:bg-[#DC201E] text-[#F8F3EC] font-mono text-[11px] font-bold uppercase tracking-[0.26em] rounded-none border-2 border-[#111010] transition-colors cursor-pointer"
          >
            <span>LAUNCH DASHBOARD</span>
            <span className="text-[#DC201E] group-hover:text-[#F8F3EC] font-bold">→</span>
          </button>
          <div className="font-mono text-[10px] uppercase tracking-[0.26em] text-[#8C8880]">
            TOPOLOGY CONVERGENCE: <span className="text-[#111010] font-bold">0.4MS</span>
          </div>
        </div>
      </div>
    </div>
  );
};
