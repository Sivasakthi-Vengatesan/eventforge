import React from 'react';

interface StageHeroProps {
  progress: number;
  onExplore: () => void;
}

export const StageHero: React.FC<StageHeroProps> = ({ progress, onExplore }) => {
  // Parallax translation for the 44px grid (upward 60px across stage)
  const gridOffsetY = -progress * 60;

  // Lockup lift (44px) and fade
  const lockupLiftY = -progress * 44;
  const lockupOpacity = Math.max(0, 1 - progress * 1.2);

  // Wordmark characters = 10 ('EVENTFORGE')
  // Sizing formula: min(clamp(52px, 15vw, 220px), calc(90vw / (10 * 0.44)))
  const wordmarkStyle: React.CSSProperties = {
    fontSize: 'min(clamp(52px, 15vw, 220px), calc(90vw / 4.4))',
    whiteSpace: 'nowrap',
    lineHeight: 0.88,
    letterSpacing: '-0.012em',
  };

  return (
    <div className="relative sticky top-0 h-[100svh] w-full overflow-hidden bg-[#F8F3EC] text-[#111010] flex flex-col justify-between select-none">
      {/* 44px Ruled Background Grid that Parallaxes Upward */}
      <div
        className="absolute inset-0 poster-grid-44 pointer-events-none z-0 transition-transform duration-75"
        style={{
          transform: `translateY(${gridOffsetY}px)`,
          height: 'calc(100% + 60px)',
          top: 0,
        }}
      />

      {/* Top Header Furniture Line */}
      <header className="relative z-10 w-full px-6 md:px-12 py-6 border-b-2 border-[#111010] flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#F8F3EC]/90 backdrop-blur-xs">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#111010]">
            EVENTFORGE SPEC // v2.4
          </span>
          <span className="w-2 h-2 bg-[#DC201E]" />
          <span className="font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
            AUTONOMOUS GATEWAY
          </span>
        </div>

        <div className="flex items-center gap-6 font-mono text-[11px] uppercase tracking-[0.26em] text-[#111010]">
          <span className="hidden md:inline text-[#8C8880]">
            INGESTION SLA: <span className="text-[#111010] font-bold">&lt; 10MS</span>
          </span>
          <button
            onClick={onExplore}
            className="hover:text-[#DC201E] underline underline-offset-4 cursor-pointer font-bold transition-colors"
          >
            ENTER CONSOLE →
          </button>
        </div>
      </header>

      {/* Main Lockup (Lifts 44px and Fades on Scroll) */}
      <div
        className="relative z-10 w-full max-w-7xl mx-auto px-6 md:px-12 my-auto flex flex-col items-start transition-all duration-75"
        style={{
          transform: `translateY(${lockupLiftY}px)`,
          opacity: lockupOpacity,
        }}
      >
        {/* Mono Kicker */}
        <div className="font-mono text-[11px] md:text-[12px] font-bold uppercase tracking-[0.26em] text-[#8C8880] mb-4">
          // ZERO-LOSS EVENT INGESTION & RELIABILITY INFRASTRUCTURE
        </div>

        {/* Scaled Anton Wordmark (Second half in red) */}
        <h1
          className="font-anton font-bold uppercase text-[#111010] m-0 w-full"
          style={wordmarkStyle}
        >
          EVENT<span className="text-[#DC201E]">FORGE</span>
        </h1>

        {/* 2px Ink Rule */}
        <div className="w-full border-b-2 border-[#111010] my-8" />

        {/* Under-Rule Two Column Block */}
        <div className="w-full grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          <div className="md:col-span-8">
            <p className="font-archivo text-[15px] md:text-[18px] leading-[1.6] text-[#111010] m-0 max-w-2xl font-normal">
              A time-promise distributed event ingestion gateway. We decouple high-velocity webhooks from processing backpressure, prevent duplicate financial mutations, and autonomously throttle or scale worker fleets to guarantee zero packet loss under downstream outage conditions.
            </p>
          </div>

          <div className="md:col-span-4 flex flex-col items-start md:items-end gap-3">
            <button
              onClick={onExplore}
              className="group relative inline-flex items-center gap-3 px-8 py-4 bg-[#111010] hover:bg-[#DC201E] active:bg-[#111010] text-[#F8F3EC] font-mono text-[12px] font-bold uppercase tracking-[0.26em] rounded-none border-2 border-[#111010] transition-colors cursor-pointer"
            >
              <span>EXPLORE PLATFORM</span>
              <span className="text-[#DC201E] group-hover:text-[#F8F3EC] transition-colors font-bold">→</span>
            </button>
            <span className="font-mono text-[10px] uppercase tracking-[0.26em] text-[#8C8880]">
              LIVE DEMO // REAL WEBSOCKET TELEMETRY
            </span>
          </div>
        </div>
      </div>

      {/* Hero Base with 38-Second Ambient Red Hairline */}
      <div className="relative z-10 w-full border-t border-[#111010]/20 bg-[#F8F3EC]/80 py-4 px-6 md:px-12 flex items-center justify-between font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
        <div>SCROLL DOWN TO INSPECT STAGES [1 — 4]</div>
        <div className="text-[#111010] font-bold">
          STAGE 01 // <span className="text-[#DC201E]">POSTER LOCKUP</span>
        </div>

        {/* Single 3px Ambient Red Hairline across the base */}
        <div className="absolute top-0 left-0 w-full h-[3px] overflow-hidden pointer-events-none">
          <div className="w-48 h-full bg-[#DC201E] animate-ambient-hairline" />
        </div>
      </div>
    </div>
  );
};
