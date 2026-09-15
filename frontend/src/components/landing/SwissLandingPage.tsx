import React, { useEffect } from 'react';
import { useScrollStages } from './useScrollStages';
import { StageHero } from './StageHero';
import { StageWipe } from './StageWipe';
import { StageTimeline } from './StageTimeline';
import { StageRouteMap } from './StageRouteMap';
import { NormalBands } from './NormalBands';

interface SwissLandingPageProps {
  onExplore: () => void;
}

export const SwissLandingPage: React.FC<SwissLandingPageProps> = ({ onExplore }) => {
  const { progress, stage0Ref, stage1Ref, stage2Ref, stage3Ref } = useScrollStages();

  useEffect(() => {
    // Scroll to top on mount
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="w-full min-h-screen bg-[#F8F3EC] text-[#111010] flex flex-col font-archivo selection:bg-[#DC201E] selection:text-[#F8F3EC]">
      {/* ========================================================================= */}
      {/* STAGE 1: HERO OVER 44PX RULED GRID (280svh)                               */}
      {/* ========================================================================= */}
      <section ref={stage0Ref} className="relative w-full h-[280svh] bg-[#F8F3EC]">
        <StageHero progress={progress.p0} onExplore={onExplore} />
      </section>

      {/* ========================================================================= */}
      {/* STAGE 2: LEFT-TO-RIGHT WIPE ON INK (260svh)                               */}
      {/* ========================================================================= */}
      <section ref={stage1Ref} className="relative w-full h-[260svh] bg-[#111010]">
        <StageWipe progress={progress.p1} />
      </section>

      {/* ========================================================================= */}
      {/* STAGE 3: DETERMINISTIC TIMELINE ON PAPER-ALT (400svh)                     */}
      {/* ========================================================================= */}
      <section ref={stage2Ref} className="relative w-full h-[400svh] bg-[#F1EBE1]">
        <StageTimeline progress={progress.p2} />
      </section>

      {/* ========================================================================= */}
      {/* STAGE 4: PHYLLOTAXIS TRACED ROUTE MAP (300svh)                            */}
      {/* ========================================================================= */}
      <section ref={stage3Ref} className="relative w-full h-[300svh] bg-[#F8F3EC]">
        <StageRouteMap progress={progress.p3} onExplore={onExplore} />
      </section>

      {/* ========================================================================= */}
      {/* NORMAL BANDS: EXPLAINER GRID, RATE TABLE, FAQ & CTA                       */}
      {/* ========================================================================= */}
      <NormalBands onExplore={onExplore} />
    </div>
  );
};
