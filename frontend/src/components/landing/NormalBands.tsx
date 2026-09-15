import React, { useEffect, useRef } from 'react';
import { SplitText } from './TextSplitter';

interface NormalBandsProps {
  onExplore: () => void;
}

export const NormalBands: React.FC<NormalBandsProps> = ({ onExplore }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed');
          }
        });
      },
      { threshold: 0.12 }
    );

    const revElements = el.querySelectorAll('[data-rev]');
    revElements.forEach((target) => observer.observe(target));

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div ref={containerRef} className="w-full bg-[#F8F3EC] text-[#111010] flex flex-col items-center">
      {/* ========================================================================= */}
      {/* 1. THREE-CELL EXPLAINER GRID (Separated by 1px hairline gaps)             */}
      {/* ========================================================================= */}
      <section className="w-full max-w-7xl px-6 md:px-12 py-20 border-b-2 border-[#111010]">
        <div className="mb-12">
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#8C8880] mb-3" data-rev style={{ '--d': '40ms' } as React.CSSProperties}>
            // ARCHITECTURAL FOUNDATIONS
          </div>
          <SplitText
            as="h2"
            text="THREE INVARIANTS OF RESILIENT INGESTION"
            className="font-anton uppercase tracking-[-0.012em] text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-[#111010] leading-[0.90] m-0"
            highlightWords={['RESILIENT', 'INVARIANTS']}
            baseDelayMs={80}
            staggerMs={36}
          />
        </div>

        {/* 3-cell Grid with 1px Hairline Gaps */}
        <div className="grid grid-cols-1 md:grid-cols-3 bg-[#111010]/20 gap-[1px] border border-[#111010]/20">
          {/* Cell 1 */}
          <div className="bg-[#F8F3EC] p-8 flex flex-col justify-between" data-rev style={{ '--d': '80ms' } as React.CSSProperties}>
            <div>
              <div className="flex items-center justify-between border-b border-[#111010]/20 pb-4 mb-6">
                <span className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#DC201E]">
                  PRIMITIVE 01
                </span>
                <span className="font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
                  REDIS STREAMS + PEL
                </span>
              </div>
              <h3 className="font-anton uppercase tracking-[-0.012em] text-2xl text-[#111010] leading-[0.94] mb-4">
                DURABLE CONSUMER GROUPS
              </h3>
              <p className="font-archivo text-[15px] leading-[1.6] text-[#111010]/80 m-0">
                Every webhook payload is appended to an append-only Redis Stream with deterministic IDs. Pending Entries Lists (PEL) track in-flight tasks and reassign stalled leases without duplication.
              </p>
            </div>
            <div className="mt-8 pt-4 border-t border-[#111010]/10 font-mono text-[10px] uppercase tracking-[0.26em] text-[#8C8880]">
              ZERO DISK CHURN // IN-MEMORY PEL
            </div>
          </div>

          {/* Cell 2 */}
          <div className="bg-[#F8F3EC] p-8 flex flex-col justify-between" data-rev style={{ '--d': '160ms' } as React.CSSProperties}>
            <div>
              <div className="flex items-center justify-between border-b border-[#111010]/20 pb-4 mb-6">
                <span className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#DC201E]">
                  PRIMITIVE 02
                </span>
                <span className="font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
                  TOKEN BUCKET LEAK
                </span>
              </div>
              <h3 className="font-anton uppercase tracking-[-0.012em] text-2xl text-[#111010] leading-[0.94] mb-4">
                ADAPTIVE BACKPRESSURE
              </h3>
              <p className="font-archivo text-[15px] leading-[1.6] text-[#111010]/80 m-0">
                High-priority financial mutations bypass non-critical analytics. When downstream error rates climb beyond 25%, the platform engages dynamic batching and throttles ingest rates automatically.
              </p>
            </div>
            <div className="mt-8 pt-4 border-t border-[#111010]/10 font-mono text-[10px] uppercase tracking-[0.26em] text-[#8C8880]">
              PRIORITY LEVELS [CRITICAL / HIGH / LOW]
            </div>
          </div>

          {/* Cell 3 */}
          <div className="bg-[#F8F3EC] p-8 flex flex-col justify-between" data-rev style={{ '--d': '240ms' } as React.CSSProperties}>
            <div>
              <div className="flex items-center justify-between border-b border-[#111010]/20 pb-4 mb-6">
                <span className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#DC201E]">
                  PRIMITIVE 03
                </span>
                <span className="font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
                  DLQ + DRIFT RADAR
                </span>
              </div>
              <h3 className="font-anton uppercase tracking-[-0.012em] text-2xl text-[#111010] leading-[0.94] mb-4">
                ISOLATED POISON CONTAINMENT
              </h3>
              <p className="font-archivo text-[15px] leading-[1.6] text-[#111010]/80 m-0">
                Poison pills and malformed JSON payloads are quarantined to a Dead Letter Queue (DLQ) after 3 exponential backoff retries, ensuring the healthy queue pipeline continues moving unhindered.
              </p>
            </div>
            <div className="mt-8 pt-4 border-t border-[#111010]/10 font-mono text-[10px] uppercase tracking-[0.26em] text-[#8C8880]">
              REPLAY CAPABILITY // ONE-CLICK RE-INGEST
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 2. RATE & SLA TABLE (Ruled rows with mono red figures)                   */}
      {/* ========================================================================= */}
      <section className="w-full max-w-7xl px-6 md:px-12 py-20 border-b-2 border-[#111010]">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
          <div>
            <div className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#8C8880] mb-3" data-rev style={{ '--d': '40ms' } as React.CSSProperties}>
              // PERFORMANCE & GUARANTEES
            </div>
            <SplitText
              as="h2"
              text="MEASURED BENCHMARKS & OPERATING TIERS"
              className="font-anton uppercase tracking-[-0.012em] text-3xl sm:text-4xl md:text-5xl text-[#111010] leading-[0.90] m-0"
              highlightWords={['BENCHMARKS', 'TIERS']}
              baseDelayMs={60}
              staggerMs={36}
            />
          </div>
          <div className="font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]" data-rev style={{ '--d': '120ms' } as React.CSSProperties}>
            STRICT ZERO-LOSS SLA SPECIFICATION
          </div>
        </div>

        {/* Rate Table with 2px Ink Rules and 1px Hairlines */}
        <div className="w-full border-t-2 border-b-2 border-[#111010]">
          {/* Table Header */}
          <div className="grid grid-cols-12 gap-4 py-4 px-3 border-b-2 border-[#111010] bg-[#F1EBE1] font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880] font-bold">
            <div className="col-span-4 md:col-span-3 text-[#111010]">METRIC / TIER</div>
            <div className="col-span-5 md:col-span-6 hidden sm:block">ARCHITECTURAL SPECIFICATION</div>
            <div className="col-span-8 sm:col-span-3 text-right text-[#DC201E]">MEASURED RESULT</div>
          </div>

          {/* Row 1 */}
          <div className="grid grid-cols-12 gap-4 py-5 px-3 border-b border-[#111010]/20 items-center hover:bg-[#F1EBE1]/50 transition-colors" data-rev style={{ '--d': '40ms' } as React.CSSProperties}>
            <div className="col-span-4 md:col-span-3 font-anton uppercase text-lg sm:text-xl text-[#111010] tracking-[-0.012em]">
              INGESTION LATENCY (P99)
            </div>
            <div className="col-span-5 md:col-span-6 hidden sm:block font-archivo text-[14px] text-[#8C8880]">
              End-to-end HTTP POST ingress through HMAC signature verification and atomic Redis XADD buffer.
            </div>
            <div className="col-span-8 sm:col-span-3 text-right font-mono text-[13px] md:text-[14px] font-bold uppercase tracking-[0.20em] text-[#DC201E]">
              &lt; 8.4MS
            </div>
          </div>

          {/* Row 2 */}
          <div className="grid grid-cols-12 gap-4 py-5 px-3 border-b border-[#111010]/20 items-center hover:bg-[#F1EBE1]/50 transition-colors" data-rev style={{ '--d': '80ms' } as React.CSSProperties}>
            <div className="col-span-4 md:col-span-3 font-anton uppercase text-lg sm:text-xl text-[#111010] tracking-[-0.012em]">
              PEAK CONCURRENT EPS
            </div>
            <div className="col-span-5 md:col-span-6 hidden sm:block font-archivo text-[14px] text-[#8C8880]">
              Maximum sustained raw ingest throughput per node cluster before backpressure shedding is triggered.
            </div>
            <div className="col-span-8 sm:col-span-3 text-right font-mono text-[13px] md:text-[14px] font-bold uppercase tracking-[0.20em] text-[#DC201E]">
              12,500 REQ/S
            </div>
          </div>

          {/* Row 3 */}
          <div className="grid grid-cols-12 gap-4 py-5 px-3 border-b border-[#111010]/20 items-center hover:bg-[#F1EBE1]/50 transition-colors" data-rev style={{ '--d': '120ms' } as React.CSSProperties}>
            <div className="col-span-4 md:col-span-3 font-anton uppercase text-lg sm:text-xl text-[#111010] tracking-[-0.012em]">
              DUPLICATE RATE UNDER RETRY
            </div>
            <div className="col-span-5 md:col-span-6 hidden sm:block font-archivo text-[14px] text-[#8C8880]">
              Idempotency key enforcement using distributed atomic locks across concurrent webhook payloads.
            </div>
            <div className="col-span-8 sm:col-span-3 text-right font-mono text-[13px] md:text-[14px] font-bold uppercase tracking-[0.20em] text-[#DC201E]">
              0.0000%
            </div>
          </div>

          {/* Row 4 */}
          <div className="grid grid-cols-12 gap-4 py-5 px-3 border-b border-[#111010]/20 items-center hover:bg-[#F1EBE1]/50 transition-colors" data-rev style={{ '--d': '160ms' } as React.CSSProperties}>
            <div className="col-span-4 md:col-span-3 font-anton uppercase text-lg sm:text-xl text-[#111010] tracking-[-0.012em]">
              CIRCUIT BREAKER TRIP TIME
            </div>
            <div className="col-span-5 md:col-span-6 hidden sm:block font-archivo text-[14px] text-[#8C8880]">
              Automated trip threshold when downstream 5xx errors exceed 20% over 50 consecutive calls.
            </div>
            <div className="col-span-8 sm:col-span-3 text-right font-mono text-[13px] md:text-[14px] font-bold uppercase tracking-[0.20em] text-[#DC201E]">
              12.0MS
            </div>
          </div>

          {/* Row 5 */}
          <div className="grid grid-cols-12 gap-4 py-5 px-3 items-center hover:bg-[#F1EBE1]/50 transition-colors" data-rev style={{ '--d': '200ms' } as React.CSSProperties}>
            <div className="col-span-4 md:col-span-3 font-anton uppercase text-lg sm:text-xl text-[#111010] tracking-[-0.012em]">
              POISON ISOLATION SPEED
            </div>
            <div className="col-span-5 md:col-span-6 hidden sm:block font-archivo text-[14px] text-[#8C8880]">
              Time to isolate corrupt payloads into Dead Letter Queue without stalling sibling stream items.
            </div>
            <div className="col-span-8 sm:col-span-3 text-right font-mono text-[13px] md:text-[14px] font-bold uppercase tracking-[0.20em] text-[#DC201E]">
              &lt; 3.0MS
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. FAQ SECTION (Native details rows with CSS-only plus)                   */}
      {/* ========================================================================= */}
      <section className="w-full max-w-7xl px-6 md:px-12 py-20 border-b-2 border-[#111010]">
        <div className="mb-12">
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#8C8880] mb-3" data-rev style={{ '--d': '40ms' } as React.CSSProperties}>
            // FREQUENTLY ANSWERED INQUIRIES
          </div>
          <SplitText
            as="h2"
            text="SYSTEM CAPABILITIES & ARCHITECTURAL SPECS"
            className="font-anton uppercase tracking-[-0.012em] text-3xl sm:text-4xl md:text-5xl text-[#111010] leading-[0.90] m-0"
            highlightWords={['CAPABILITIES', 'SPECS']}
            baseDelayMs={60}
            staggerMs={36}
          />
        </div>

        {/* Native details accordion */}
        <div className="w-full border-t-2 border-[#111010] divide-y divide-[#111010]/20">
          {/* FAQ 1 */}
          <details className="group py-6 cursor-pointer" data-rev style={{ '--d': '60ms' } as React.CSSProperties}>
            <summary className="flex items-center justify-between select-none">
              <span className="font-anton uppercase text-xl sm:text-2xl text-[#111010] tracking-[-0.012em]">
                HOW DOES EVENTFORGE PREVENT DATA LOSS WHEN DOWNSTREAM SERVICES CRASH?
              </span>
              <span className="font-mono text-2xl text-[#DC201E] font-bold transition-transform duration-200 group-open:rotate-45 leading-none px-2">
                +
              </span>
            </summary>
            <div className="mt-4 pt-2 pr-12 font-archivo text-[15px] leading-[1.6] text-[#111010]/80">
              When a downstream recipient begins failing or returning 503 errors, our autonomous Circuit Breaker transitions to the OPEN state within 12 milliseconds. Webhooks continue to be safely buffered in Redis Streams with zero disk degradation. Events are never discarded; they await automatic recovery or are routed to backpressure queues.
            </div>
          </details>

          {/* FAQ 2 */}
          <details className="group py-6 cursor-pointer" data-rev style={{ '--d': '120ms' } as React.CSSProperties}>
            <summary className="flex items-center justify-between select-none">
              <span className="font-anton uppercase text-xl sm:text-2xl text-[#111010] tracking-[-0.012em]">
                CAN DUPLICATE FINANCIAL TRANSACTIONS BE ACCIDENTALLY PROCESSED?
              </span>
              <span className="font-mono text-2xl text-[#DC201E] font-bold transition-transform duration-200 group-open:rotate-45 leading-none px-2">
                +
              </span>
            </summary>
            <div className="mt-4 pt-2 pr-12 font-archivo text-[15px] leading-[1.6] text-[#111010]/80">
              No. EventForge implements an atomic two-phase idempotency guarantee. Before worker dispatch, each payload’s idempotency key or SHA-256 body hash is verified via distributed Redis locks with a 24-hour TTL. Duplicate deliveries are acknowledged immediately to sender but filtered from queue dispatch.
            </div>
          </details>

          {/* FAQ 3 */}
          <details className="group py-6 cursor-pointer" data-rev style={{ '--d': '180ms' } as React.CSSProperties}>
            <summary className="flex items-center justify-between select-none">
              <span className="font-anton uppercase text-xl sm:text-2xl text-[#111010] tracking-[-0.012em]">
                HOW DOES DYNAMIC WORKER AUTOSCALING REACT TO QUEUE SPIKES?
              </span>
              <span className="font-mono text-2xl text-[#DC201E] font-bold transition-transform duration-200 group-open:rotate-45 leading-none px-2">
                +
              </span>
            </summary>
            <div className="mt-4 pt-2 pr-12 font-archivo text-[15px] leading-[1.6] text-[#111010]/80">
              Our telemetry loop measures stream lag and consumer latency every 1,000ms. If queue depth exceeds 500 unprocessed items, the worker fleet scales up to 8 parallel consumer workers across active CPU cores, dropping back down to idle 2-worker pools once pressure normalizes.
            </div>
          </details>

          {/* FAQ 4 */}
          <details className="group py-6 cursor-pointer" data-rev style={{ '--d': '240ms' } as React.CSSProperties}>
            <summary className="flex items-center justify-between select-none">
              <span className="font-anton uppercase text-xl sm:text-2xl text-[#111010] tracking-[-0.012em]">
                WHAT HAPPENS TO POISON PILLS OR MALFORMED JSON BODIES?
              </span>
              <span className="font-mono text-2xl text-[#DC201E] font-bold transition-transform duration-200 group-open:rotate-45 leading-none px-2">
                +
              </span>
            </summary>
            <div className="mt-4 pt-2 pr-12 font-archivo text-[15px] leading-[1.6] text-[#111010]/80">
              Poison payloads that fail schema validation or throw unhandled exceptions are quarantined to our Dead Letter Queue (DLQ). Operators can view full stack traces, inspect raw payload bytes, and trigger single-item or bulk replays directly through the EventForge interactive console.
            </div>
          </details>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. FINAL CALL TO ACTION (Swiss Poster Mark)                               */}
      {/* ========================================================================= */}
      <section className="w-full max-w-7xl px-6 md:px-12 py-24 flex flex-col md:flex-row md:items-center justify-between gap-12">
        <div className="max-w-2xl">
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.26em] text-[#8C8880] mb-3" data-rev style={{ '--d': '40ms' } as React.CSSProperties}>
            // READY TO TEST REAL TELEMETRY
          </div>
          <SplitText
            as="h2"
            text="EXPERIENCE THE LIVE ADAPTIVE ENGINE"
            className="font-anton uppercase tracking-[-0.012em] text-4xl sm:text-5xl md:text-6xl text-[#111010] leading-[0.88] m-0"
            highlightWords={['EXPERIENCE', 'ADAPTIVE', 'ENGINE']}
            baseDelayMs={80}
            staggerMs={36}
          />
          <p className="font-archivo text-[16px] leading-[1.6] text-[#111010]/80 mt-4 max-w-xl" data-rev style={{ '--d': '160ms' } as React.CSSProperties}>
            Enter the interactive operator console. Simulate bursts up to 2,000 req/s, inject network partition failures, trip circuit breakers, and monitor Redis Stream telemetry in real-time.
          </p>
        </div>

        <div className="flex flex-col items-start md:items-end gap-4 shrink-0" data-rev style={{ '--d': '200ms' } as React.CSSProperties}>
          <button
            onClick={onExplore}
            className="group relative inline-flex items-center gap-4 px-10 py-5 bg-[#111010] hover:bg-[#DC201E] active:bg-[#111010] text-[#F8F3EC] font-mono text-[13px] font-bold uppercase tracking-[0.26em] rounded-none border-2 border-[#111010] transition-colors cursor-pointer shadow-none"
          >
            <span>ENTER PLATFORM CONSOLE</span>
            <span className="text-[#DC201E] group-hover:text-[#F8F3EC] transition-colors font-bold text-lg">→</span>
          </button>
          <div className="font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
            NO REGISTRATION REQUIRED // INSTANT ACCESS
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. MINIMAL FOOTER                                                         */}
      {/* ========================================================================= */}
      <footer className="w-full border-t-2 border-[#111010] bg-[#F1EBE1] py-8 px-6 md:px-12">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 font-mono text-[11px] uppercase tracking-[0.26em] text-[#8C8880]">
          <div className="flex items-center gap-3">
            <span className="text-[#111010] font-bold">EVENTFORGE</span>
            <span>//</span>
            <span>SWISS POSTER SYSTEM</span>
          </div>
          <div>
            RELIABILITY INGESTION GATEWAY // 2026
          </div>
          <div className="flex items-center gap-4 text-[#111010]">
            <button onClick={onExplore} className="hover:text-[#DC201E] underline underline-offset-4 cursor-pointer">
              OPERATOR CONSOLE
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
