import React from 'react';

interface StageTimelineProps {
  progress: number;
}

interface TimelineEvent {
  timeSeconds: number; // For mathematical interpolation
  timeFormatted: string;
  label: string;
  note: string;
  status: string;
  rateEps: number;
  eventsCount: number;
}

const TIMELINE_SERIES: TimelineEvent[] = [
  {
    timeSeconds: 0.0,
    timeFormatted: '00:00.00',
    label: 'INGESTION & HMAC',
    note: 'SHA-256 VERIFIED IN 2.1MS',
    status: 'SECURITY VERIFIED',
    rateEps: 12.0,
    eventsCount: 200,
  },
  {
    timeSeconds: 0.08,
    timeFormatted: '00:00.08',
    label: 'IDEMPOTENCY LOCK',
    note: 'ATOMIC DEDUP CHECK & STORE',
    status: 'IDEMPOTENCY CONFIRMED',
    rateEps: 24.5,
    eventsCount: 480,
  },
  {
    timeSeconds: 0.14,
    timeFormatted: '00:00.14',
    label: 'REDIS STREAM BUFFER',
    note: 'XADD CONSUMER GROUP ASSIGN',
    status: 'STREAM BUFFERED',
    rateEps: 38.2,
    eventsCount: 850,
  },
  {
    timeSeconds: 1.20,
    timeFormatted: '00:01.20',
    label: 'ADAPTIVE DISPATCH',
    note: 'PRIORITY ROUTING & CIRCUIT CHECK',
    status: 'ADAPTIVE DISPATCHED',
    rateEps: 48.6,
    eventsCount: 1240,
  },
  {
    timeSeconds: 2.50,
    timeFormatted: '00:02.50',
    label: 'ACID COMMIT & ACK',
    note: 'PEL CLEARED & ZERO DRIFT',
    status: 'ACID ACKNOWLEDGED',
    rateEps: 52.4,
    eventsCount: 1420,
  },
];

export const StageTimeline: React.FC<StageTimelineProps> = ({ progress }) => {
  // Clamped progress [0, 1]
  const p = Math.max(0, Math.min(1, progress));

  // Determine active row index [0..4]
  const activeIndex = Math.min(4, Math.floor(p * 5));

  // Interpolate continuous time from the single series
  // Piecewise linear interpolation across the 5 marks
  const numIntervals = TIMELINE_SERIES.length - 1;
  const scaledP = p * numIntervals;
  const lowerIndex = Math.min(numIntervals - 1, Math.floor(scaledP));
  const frac = scaledP - lowerIndex;

  const t0 = TIMELINE_SERIES[lowerIndex].timeSeconds;
  const t1 = TIMELINE_SERIES[Math.min(lowerIndex + 1, TIMELINE_SERIES.length - 1)].timeSeconds;
  const interpolatedSeconds = t0 + (t1 - t0) * frac;

  // Format mm:ss.SS
  const mins = Math.floor(interpolatedSeconds / 60);
  const secs = Math.floor(interpolatedSeconds % 60);
  const hundredths = Math.floor((interpolatedSeconds % 1) * 100);
  const clockDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(hundredths).padStart(2, '0')}`;

  // Interpolate EPS rate and event count from the exact same series
  const r0 = TIMELINE_SERIES[lowerIndex].rateEps;
  const r1 = TIMELINE_SERIES[Math.min(lowerIndex + 1, TIMELINE_SERIES.length - 1)].rateEps;
  const currentEps = (r0 + (r1 - r0) * frac).toFixed(1);

  const c0 = TIMELINE_SERIES[lowerIndex].eventsCount;
  const c1 = TIMELINE_SERIES[Math.min(lowerIndex + 1, TIMELINE_SERIES.length - 1)].eventsCount;
  const currentCount = Math.round(c0 + (c1 - c0) * frac);

  const currentStatus = TIMELINE_SERIES[activeIndex].status;

  return (
    <div className="relative sticky top-0 h-[100svh] w-full overflow-hidden bg-[#F1EBE1] text-[#111010] flex flex-col justify-between p-6 md:p-12 select-none poster-grid-44">
      {/* Top Header Furniture Line */}
      <div className="w-full flex items-center justify-between border-b-2 border-[#111010] pb-4 font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 bg-[#DC201E]" />
          <span className="text-[#111010]">STAGE 03 // DETERMINISTIC DISPATCH TIMELINE</span>
        </div>
        <div className="text-[#111010]">
          SYNCHRONIZED METRICS // <span className="text-[#DC201E] font-bold">1 SINGLE TRUTH SERIES</span>
        </div>
      </div>

      {/* Main Two-Column Stage Content */}
      <div className="my-auto w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Column: Headline & Cumulative Lit Ruled Rows (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#8C8880]">
            // SUB-SECOND EXECUTION TELEMETRY
          </div>

          <h2 className="font-anton uppercase tracking-[-0.012em] leading-[0.90] text-[#111010] text-3xl sm:text-4xl md:text-5xl lg:text-6xl m-0">
            DETERMINISTIC INGESTION <span className="text-[#DC201E]">UNDER REAL LOAD</span>
          </h2>

          <p className="font-archivo text-[15px] leading-[1.6] text-[#111010]/80 max-w-xl">
            Each event transitions through strict verifiable milestones. Every worker heartbeat, stream offset acknowledgment, and state commit is serialized without race conditions.
          </p>

          {/* 5 Ruled Rows Lighting Cumulatively as floor(p * 5) advances */}
          <div className="border-t-2 border-b-2 border-[#111010] divide-y divide-[#111010]/20 mt-2">
            {TIMELINE_SERIES.map((item, index) => {
              const isLit = index <= activeIndex;
              const isCurrent = index === activeIndex;

              return (
                <div
                  key={index}
                  className={`grid grid-cols-12 gap-4 py-3.5 px-3 items-center transition-all duration-200 ${
                    isLit ? 'opacity-100 bg-[#F8F3EC]/70' : 'opacity-30 bg-transparent'
                  }`}
                >
                  {/* Timestamp */}
                  <div className="col-span-3 font-mono text-[11px] font-bold uppercase tracking-[0.20em]">
                    <span className={isLit ? 'text-[#DC201E]' : 'text-[#8C8880]'}>
                      {item.timeFormatted}
                    </span>
                  </div>

                  {/* Anton Label */}
                  <div className="col-span-5 font-anton text-base md:text-lg tracking-[-0.012em] text-[#111010] flex items-center gap-2">
                    {isCurrent && <span className="w-1.5 h-1.5 bg-[#DC201E] inline-block" />}
                    <span>{item.label}</span>
                  </div>

                  {/* Mono Note */}
                  <div className="col-span-4 font-mono text-[10px] md:text-[11px] uppercase tracking-[0.20em] text-[#8C8880] text-right truncate">
                    {item.note}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: 2px-Bordered Square Clock Panel (5 cols) */}
        <div className="lg:col-span-5 flex justify-center">
          <div className="relative w-full max-w-md aspect-square bg-[#F8F3EC] border-2 border-[#111010] p-8 flex flex-col justify-between select-none">
            {/* Top Bar inside Panel */}
            <div className="flex items-center justify-between border-b border-[#111010]/20 pb-4 font-mono text-[10px] md:text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
              <span className="text-[#111010] font-bold">RUN // EF-9082-AUTONOMOUS</span>
              <span className="text-[#DC201E] font-bold">{currentStatus}</span>
            </div>

            {/* Center Elapsed Clock */}
            <div className="my-auto text-center py-4">
              <span className="font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880] block mb-2">
                ELAPSED TIME (INTERPOLATED)
              </span>
              <div className="font-anton text-6xl sm:text-7xl lg:text-8xl tracking-[-0.012em] text-[#DC201E] leading-none">
                {clockDisplay}
              </div>
              <div className="mt-4 font-mono text-[12px] font-bold uppercase tracking-[0.26em] text-[#111010]">
                {currentEps} EPS // {currentCount.toLocaleString()} EVENTS
              </div>
            </div>

            {/* Bottom Meta & 6px Red Meter */}
            <div className="border-t border-[#111010]/20 pt-4 font-mono text-[10px] uppercase tracking-[0.26em] text-[#8C8880] flex justify-between">
              <span>ZERO INGESTION DRIFT</span>
              <span className="text-[#111010] font-bold">{Math.round(p * 100)}% COMPLETE</span>
            </div>

            {/* 6px Red Meter along panel base */}
            <div
              className="absolute bottom-0 left-0 h-[6px] bg-[#DC201E] transition-all duration-75"
              style={{
                width: `${p * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Bottom Stage Footnote */}
      <div className="w-full flex items-center justify-between border-t-2 border-[#111010] pt-4 font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
        <div>STAGE 03 COMPLETE // INTERPOLATED TIME-PROMISE SPEC</div>
        <div className="text-[#111010]">SCROLL TO OBSERVE STAGE 04 [TRACED ROUTE MAP]</div>
      </div>
    </div>
  );
};
