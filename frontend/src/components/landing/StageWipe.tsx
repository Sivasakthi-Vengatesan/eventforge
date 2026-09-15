import React from 'react';

interface StageWipeProps {
  progress: number;
}

export const StageWipe: React.FC<StageWipeProps> = ({ progress }) => {
  // Statement text to wipe left-to-right
  const statementText = "EVENTS IN. FAILURES OUT. ZERO DRIFT.";

  // Compute clip percentage (0% to 100%)
  const clipPercent = Math.max(0, Math.min(100, progress * 100));

  return (
    <div className="relative sticky top-0 h-[100svh] w-full overflow-hidden bg-[#111010] text-[#F8F3EC] flex flex-col justify-between p-6 md:p-12 select-none poster-grid-44-dark">
      {/* Top Meta Line */}
      <div className="w-full flex items-center justify-between border-b border-[#F8F3EC]/20 pb-4 font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 bg-[#DC201E]" />
          <span className="text-[#F8F3EC]">STAGE 02 // REAL-TIME INGESTION GUARANTEE</span>
        </div>
        <div className="text-[#F8F3EC]/60">
          WIPE PROGRESS: <span className="text-[#DC201E] font-bold">{Math.round(clipPercent)}%</span>
        </div>
      </div>

      {/* Center Wipe Statement Block */}
      <div className="my-auto w-full max-w-7xl mx-auto py-8">
        <div className="relative w-full">
          {/* Base Layer: 18% opacity paper */}
          <div
            className="font-anton uppercase tracking-[-0.012em] leading-[0.88] select-none"
            style={{
              fontSize: 'clamp(2.1rem, 7.4vw, 7.2rem)',
              color: 'rgba(248, 243, 236, 0.18)',
              maxWidth: '16ch',
            }}
          >
            {statementText}
          </div>

          {/* Exact Clone Layer: 100% full paper, clipped Left-to-Right by scroll progress */}
          <div
            className="absolute top-0 left-0 w-full font-anton uppercase tracking-[-0.012em] leading-[0.88] select-none text-[#F8F3EC] pointer-events-none"
            style={{
              fontSize: 'clamp(2.1rem, 7.4vw, 7.2rem)',
              maxWidth: '16ch',
              clipPath: `inset(0 calc(100% - ${clipPercent}%) 0 0)`,
              WebkitClipPath: `inset(0 calc(100% - ${clipPercent}%) 0 0)`,
              transition: 'clip-path 40ms linear',
            }}
          >
            {statementText}
          </div>
        </div>

        {/* 2px Paper Rule */}
        <div className="w-full border-b-2 border-[#F8F3EC] mt-12 mb-8" />

        {/* Two Mono Facts (Numbers over adjectives) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 font-mono text-[11px] md:text-[12px] uppercase tracking-[0.26em]">
          <div className="border-l-2 border-[#DC201E] pl-4 space-y-1">
            <span className="text-[#8C8880] block">FACT 01 // THROUGHPUT & LATENCY SLA</span>
            <span className="text-[#F8F3EC] font-bold block">
              9.8MS P95 INGESTION SLA // 0.00% TAIL LOSS AT 2,500 REQ/SEC
            </span>
          </div>

          <div className="border-l-2 border-[#F8F3EC]/40 pl-4 space-y-1">
            <span className="text-[#8C8880] block">FACT 02 // ELASTIC SCALING & DEDUP</span>
            <span className="text-[#F8F3EC] font-bold block">
              2 TO 8 CORES ELASTIC SCALING // 100% IDEMPOTENT DEDUPLICATION
            </span>
          </div>
        </div>
      </div>

      {/* Bottom Stage Tag */}
      <div className="w-full flex items-center justify-between border-t border-[#F8F3EC]/20 pt-4 font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
        <div>INK REGISTER // ZERO DATA LOSS PROTOCOL</div>
        <div className="text-[#F8F3EC]">SCROLL TO OBSERVE STAGE 03 [LIVE TIMELINE]</div>
      </div>
    </div>
  );
};
