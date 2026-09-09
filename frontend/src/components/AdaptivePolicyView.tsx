import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SystemMetrics, SystemMode, PolicyDecisionItem } from '../types';

interface AdaptivePolicyViewProps {
  metrics: SystemMetrics | null;
}

export const AdaptivePolicyView: React.FC<AdaptivePolicyViewProps> = ({ metrics }) => {
  const [decisions, setDecisions] = useState<PolicyDecisionItem[]>([]);
  const [selectedMode, setSelectedMode] = useState<SystemMode | 'AUTO'>('AUTO');
  const [isUpdating, setIsUpdating] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchDecisions = async () => {
    try {
      const res = await fetch('/api/v1/policies/decisions?limit=10');
      if (res.ok) {
        const data = await res.json();
        setDecisions(data);
      }
    } catch (e) {
      console.error('Failed to fetch policy decisions', e);
    }
  };

  useEffect(() => {
    fetchDecisions();
    const interval = setInterval(fetchDecisions, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleModeOverride = async (mode: SystemMode | 'AUTO') => {
    setIsUpdating(true);
    setStatusMessage(null);
    try {
      if (mode === 'AUTO') {
        const res = await fetch('/api/v1/policies/auto', { method: 'POST' });
        if (res.ok) {
          setSelectedMode('AUTO');
          setStatusMessage('SYSTEM RETURNED TO DYNAMIC AUTONOMOUS EVALUATION');
        }
      } else {
        const res = await fetch('/api/v1/policies/override', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode }),
        });
        if (res.ok) {
          setSelectedMode(mode);
          setStatusMessage(`MANUAL OVERRIDE APPLIED: ${mode} MODE ENFORCED`);
        }
      }
      fetchDecisions();
    } catch (e) {
      setStatusMessage('OVERRIDE REQUEST FAILED: NETWORK / BACKEND ERROR');
    } finally {
      setIsUpdating(false);
      setTimeout(() => setStatusMessage(null), 4000);
    }
  };

  const currentMode = metrics?.system_mode || 'NORMAL';
  const concurrency = metrics?.current_concurrency || metrics?.active_workers || 4;
  const targetConcurrency = metrics?.target_concurrency || concurrency;
  const backpressureDelay = metrics?.backpressure_delay_ms || 0;
  const retryMultiplier = metrics?.retry_backoff_multiplier || 1.0;

  const modeColorMap: Record<SystemMode, { bg: string; text: string; border: string; dot: string; desc: string }> = {
    NORMAL: {
      bg: 'bg-white',
      text: 'text-black',
      border: 'border-black',
      dot: 'bg-emerald-500',
      desc: 'Baseline nominal operation. Standard queue processing, normal concurrency (4 workers), 0ms backpressure delay.'
    },
    PRESSURE: {
      bg: 'bg-amber-50',
      text: 'text-amber-950',
      border: 'border-amber-500',
      dot: 'bg-amber-500',
      desc: 'High queue depth (>50) or elevated p95 latency (>400ms). Dynamic worker scaling to 8 workers, low-priority events throttled.'
    },
    DEGRADED: {
      bg: 'bg-black',
      text: 'text-white',
      border: 'border-swiss-accent',
      dot: 'bg-swiss-accent',
      desc: 'Downstream 429 rate limits or circuit trip. Concurrency clamped to 2, retry multiplier elevated (3.0x), exponential backpressure active.'
    },
    RECOVERY: {
      bg: 'bg-blue-50',
      text: 'text-blue-950',
      border: 'border-blue-600',
      dot: 'bg-blue-600',
      desc: 'Cooldown stabilization phase. Gradual step-up in concurrency, half-open probe requests, telemetry monitoring for healthy stabilization.'
    }
  };

  const currentModeConfig = modeColorMap[currentMode] || modeColorMap.NORMAL;

  return (
    <section id="adaptive-policy" className="py-20 px-6 md:px-12 lg:px-20 max-w-7xl mx-auto border-b-4 border-black">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 pb-6 border-b-2 border-black gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-xs font-black uppercase tracking-widest text-swiss-accent">
              SECTION 02 // AUTONOMOUS RELIABILITY
            </span>
            <span className="h-1.5 w-1.5 bg-black" />
            <span className="font-mono text-xs uppercase font-bold text-neutral-500">
              REAL-TIME CONTROL LOOP
            </span>
          </div>
          <h2 className="text-4xl md:text-5xl font-black uppercase tracking-tight text-black">
            Adaptive Policy Engine
          </h2>
          <p className="text-sm md:text-base font-bold text-neutral-600 uppercase tracking-wide mt-2 max-w-3xl">
            Autonomous dynamic feedback loop that continuously observes queue depth, downstream latency, and rate-limit friction to dynamically adjust worker concurrency, priority queue routing, and retry backoff multipliers.
          </p>
        </div>

        {/* Live Status Badge */}
        <div className="flex flex-col items-start md:items-end">
          <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 tracking-wider mb-1">
            CURRENT SYSTEM STATE
          </span>
          <div className={`flex items-center gap-3 px-4 py-2 border-2 ${currentModeConfig.border} ${currentModeConfig.bg}`}>
            <span className={`w-3 h-3 ${currentModeConfig.dot} animate-ping rounded-none`} />
            <span className={`text-lg font-mono font-black uppercase tracking-wider ${currentModeConfig.text}`}>
              {currentMode} MODE
            </span>
          </div>
        </div>
      </div>

      {/* Grid: Dynamic Gauges & Controller States */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
        {/* Left Column: Live Control Parameters (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="border-2 border-black p-6 bg-neutral-50">
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-black/20">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-black">
                DYNAMIC WORKER CONCURRENCY FLEET
              </span>
              <span className="text-xs font-mono font-bold text-neutral-500">
                RANGE: 2 - 8 CORES
              </span>
            </div>

            {/* Concurrency Visualizer */}
            <div className="flex items-center gap-6 mb-6">
              <div className="text-5xl font-mono font-black text-black">
                {concurrency}
                <span className="text-base text-neutral-500 font-normal"> / 8 CORES</span>
              </div>
              <div className="flex-1">
                <div className="flex justify-between text-[11px] font-mono font-bold mb-2">
                  <span>CONCURRENCY UTILIZATION</span>
                  <span className="text-swiss-accent font-black">
                    {targetConcurrency !== concurrency ? `TARGET: ${targetConcurrency}` : 'STABLE'}
                  </span>
                </div>
                <div className="h-5 w-full bg-white border-2 border-black flex gap-1 p-0.5">
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                    <div
                      key={i}
                      className={`flex-1 transition-all duration-300 ${
                        i <= concurrency
                          ? currentMode === 'DEGRADED'
                            ? 'bg-swiss-accent'
                            : 'bg-black'
                          : 'bg-neutral-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>

            <p className="text-xs font-mono text-neutral-700 leading-relaxed uppercase border-t border-black/10 pt-4">
              {currentModeConfig.desc}
            </p>
          </div>

          {/* 3 Metric Sub-Panels */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border-2 border-black p-4 bg-white">
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block mb-1">
                BACKPRESSURE DELAY
              </span>
              <div className="text-2xl font-mono font-black text-black">
                {backpressureDelay} <span className="text-xs font-normal text-neutral-500">ms</span>
              </div>
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-400 mt-1 block">
                {backpressureDelay > 0 ? 'ACTIVE SHEDDING' : 'ZERO INGESTION LAG'}
              </span>
            </div>

            <div className="border-2 border-black p-4 bg-white">
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block mb-1">
                RETRY MULTIPLIER
              </span>
              <div className="text-2xl font-mono font-black text-black">
                {retryMultiplier.toFixed(1)}x
              </div>
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-400 mt-1 block">
                {retryMultiplier > 1.0 ? 'ELEVATED BACKOFF' : 'BASE 2.0s EXPONENTIAL'}
              </span>
            </div>

            <div className="border-2 border-black p-4 bg-white">
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block mb-1">
                BATCH BUFFER
              </span>
              <div className="text-2xl font-mono font-black text-black">
                {metrics?.batch_buffer_size || 0} <span className="text-xs font-normal text-neutral-500">queued</span>
              </div>
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-400 mt-1 block">
                LOW-PRIORITY PACKING
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Mode Controller & Test Overrides (5 cols) */}
        <div className="lg:col-span-5 border-2 border-black p-6 bg-white flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-black/20">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-black">
                MANUAL POLICY OVERRIDE / TESTBENCH
              </span>
              <span className="text-[10px] font-mono bg-neutral-100 border border-black px-1.5 py-0.5 font-bold">
                INTERACTIVE
              </span>
            </div>

            <p className="text-xs font-bold text-neutral-600 uppercase mb-4 leading-relaxed">
              Test adaptive behavior on demand. Force the control loop into specific operational states to observe fleet adjustments in real time:
            </p>

            <div className="grid grid-cols-2 gap-2 mb-4">
              <button
                onClick={() => handleModeOverride('AUTO')}
                disabled={isUpdating}
                className={`py-2 px-3 text-xs font-mono font-bold border-2 border-black text-left uppercase transition-all ${
                  selectedMode === 'AUTO'
                    ? 'bg-black text-white'
                    : 'bg-white text-black hover:bg-neutral-100'
                }`}
              >
                ◆ AUTO (AUTONOMOUS)
              </button>

              <button
                onClick={() => handleModeOverride('NORMAL')}
                disabled={isUpdating}
                className={`py-2 px-3 text-xs font-mono font-bold border-2 border-black text-left uppercase transition-all ${
                  selectedMode === 'NORMAL'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-white text-black hover:bg-neutral-100'
                }`}
              >
                1. NORMAL MODE
              </button>

              <button
                onClick={() => handleModeOverride('PRESSURE')}
                disabled={isUpdating}
                className={`py-2 px-3 text-xs font-mono font-bold border-2 border-black text-left uppercase transition-all ${
                  selectedMode === 'PRESSURE'
                    ? 'bg-amber-500 text-black'
                    : 'bg-white text-black hover:bg-neutral-100'
                }`}
              >
                2. PRESSURE MODE
              </button>

              <button
                onClick={() => handleModeOverride('DEGRADED')}
                disabled={isUpdating}
                className={`py-2 px-3 text-xs font-mono font-bold border-2 border-black text-left uppercase transition-all ${
                  selectedMode === 'DEGRADED'
                    ? 'bg-swiss-accent text-white'
                    : 'bg-white text-black hover:bg-neutral-100'
                }`}
              >
                3. DEGRADED MODE
              </button>

              <button
                onClick={() => handleModeOverride('RECOVERY')}
                disabled={isUpdating}
                className={`py-2 px-3 text-xs font-mono font-bold border-2 border-black text-left uppercase transition-all col-span-2 ${
                  selectedMode === 'RECOVERY'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-black hover:bg-neutral-100'
                }`}
              >
                4. RECOVERY COOLDOWN PROBE
              </button>
            </div>
          </div>

          {/* Feedback message banner */}
          <AnimatePresence>
            {statusMessage && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="p-3 bg-neutral-900 text-white border-2 border-black text-xs font-mono font-bold uppercase tracking-wider"
              >
                {statusMessage}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Decision Audit Log Table */}
      <div className="border-2 border-black">
        <div className="bg-black text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-swiss-accent">◆</span>
            <span className="text-xs font-mono font-black uppercase tracking-widest">
              EXPLAINABLE POLICY DECISION AUDIT LEDGER
            </span>
          </div>
          <span className="text-[10px] font-mono text-neutral-400 uppercase">
            LIVE LOGGING FEED (LAST 10 EVALUATIONS)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b-2 border-black bg-neutral-100 uppercase font-bold text-neutral-700">
                <th className="p-3 border-r border-black">TIMESTAMP</th>
                <th className="p-3 border-r border-black">TRANSITION</th>
                <th className="p-3 border-r border-black">TRIGGER REASON</th>
                <th className="p-3 border-r border-black">TELEMETRY (Q / P95 / ERR)</th>
                <th className="p-3 border-r border-black">CONCURRENCY</th>
                <th className="p-3">RETRY MULTIPLIER</th>
              </tr>
            </thead>
            <tbody>
              {decisions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-neutral-500 uppercase font-bold">
                    No policy decisions recorded yet. Evaluation engine running at 1.0s intervals.
                  </td>
                </tr>
              ) : (
                decisions.map((d, index) => (
                  <tr
                    key={d.decision_id || index}
                    className="border-b border-black/10 hover:bg-neutral-50 transition-colors"
                  >
                    <td className="p-3 border-r border-black/10 whitespace-nowrap text-neutral-600">
                      {new Date(d.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="p-3 border-r border-black/10 font-bold whitespace-nowrap">
                      <span className="text-neutral-500">{d.previous_mode}</span>
                      <span className="mx-1 text-black font-black">→</span>
                      <span
                        className={
                          d.target_mode === 'DEGRADED'
                            ? 'text-swiss-accent font-black'
                            : d.target_mode === 'PRESSURE'
                            ? 'text-amber-600 font-black'
                            : d.target_mode === 'RECOVERY'
                            ? 'text-blue-600 font-black'
                            : 'text-emerald-600 font-black'
                        }
                      >
                        {d.target_mode}
                      </span>
                    </td>
                    <td className="p-3 border-r border-black/10 font-semibold max-w-xs truncate text-black">
                      {d.trigger_reason}
                    </td>
                    <td className="p-3 border-r border-black/10 text-neutral-700 whitespace-nowrap">
                      Q: <span className="font-bold">{d.queue_depth}</span> | P95: <span className="font-bold">{d.p95_latency_ms.toFixed(0)}ms</span> | ERR: <span className="font-bold">{(d.error_rate * 100).toFixed(1)}%</span>
                    </td>
                    <td className="p-3 border-r border-black/10 font-bold text-center">
                      {d.concurrency_target} workers
                    </td>
                    <td className="p-3 font-bold text-center">
                      {d.retry_multiplier.toFixed(1)}x
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};
