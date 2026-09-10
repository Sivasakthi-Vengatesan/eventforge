import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CircuitBreakerStatus, CircuitBreakerState } from '../types';
import { API_BASE } from '../lib/api';

export const CircuitBreakerView: React.FC = () => {
  const [status, setStatus] = useState<CircuitBreakerStatus | null>(null);
  const [isInjecting, setIsInjecting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  // Downstream fault config states
  const [failureRate, setFailureRate] = useState<number>(0);
  const [rateLimitRate, setRateLimitRate] = useState<number>(0);
  const [latencyMs, setLatencyMs] = useState<number>(10);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/downstream/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data.circuit_breaker);
        if (data.service_config) {
          setFailureRate(data.service_config.failure_rate || 0);
          setRateLimitRate(data.service_config.rate_limit_rate || 0);
          setLatencyMs(data.service_config.latency_ms || 10);
        }
      }
    } catch (e) {
      console.error('Failed to fetch downstream status', e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleUpdateFaults = async () => {
    setIsInjecting(true);
    try {
      const res = await fetch(`${API_BASE}/downstream/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          failure_rate: failureRate,
          rate_limit_rate: rateLimitRate,
          latency_ms: latencyMs
        })
      });
      if (res.ok) {
        setFeedback('DOWNSTREAM FAULT INJECTION APPLIED');
        fetchStatus();
      }
    } catch (e) {
      setFeedback('FAULT INJECTION FAILED');
    } finally {
      setIsInjecting(false);
      setTimeout(() => setFeedback(null), 3000);
    }
  };

  const handleResetCircuit = async () => {
    try {
      const res = await fetch(`${API_BASE}/downstream/circuit-breaker/reset`, {
        method: 'POST'
      });
      if (res.ok) {
        setFeedback('CIRCUIT BREAKER FORCED TO CLOSED STATE');
        fetchStatus();
      }
    } catch (e) {
      setFeedback('RESET FAILED');
    } finally {
      setTimeout(() => setFeedback(null), 3000);
    }
  };

  const state: CircuitBreakerState = status?.state || 'CLOSED';

  const stateVisuals: Record<CircuitBreakerState, { bg: string; text: string; border: string; desc: string }> = {
    CLOSED: {
      bg: 'bg-white',
      text: 'text-black',
      border: 'border-black',
      desc: 'Normal downstream health. All event verification requests pass directly to downstream endpoints with zero fast-fail shedding.'
    },
    OPEN: {
      bg: 'bg-black',
      text: 'text-white',
      border: 'border-swiss-accent',
      desc: 'Downstream failure threshold exceeded! Circuit is tripped OPEN. Event verification fails fast locally to prevent thundering herd and cascading downstream collapse.'
    },
    HALF_OPEN: {
      bg: 'bg-amber-50',
      text: 'text-amber-950',
      border: 'border-amber-500',
      desc: 'Cooldown period elapsed. Trial probe requests are tested against downstream service to verify system recovery before closing circuit.'
    }
  };

  const currentVisual = stateVisuals[state] || stateVisuals.CLOSED;

  return (
    <section id="circuit-breaker" className="py-20 px-6 md:px-12 lg:px-20 max-w-7xl mx-auto border-b-4 border-black">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 pb-6 border-b-2 border-black gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-xs font-black uppercase tracking-widest text-swiss-accent">
              SECTION 06 // CASCADING FAILURE PREVENTION
            </span>
            <span className="h-1.5 w-1.5 bg-black" />
            <span className="font-mono text-xs uppercase font-bold text-neutral-500">
              DOWNSTREAM CIRCUIT BREAKER
            </span>
          </div>
          <h2 className="text-4xl md:text-5xl font-black uppercase tracking-tight text-black">
            Downstream Reliability
          </h2>
          <p className="text-sm md:text-base font-bold text-neutral-600 uppercase tracking-wide mt-2 max-w-3xl">
            Real-time finite state machine protects downstream APIs from cascading failure storms during outages and rate-limit violations through autonomous trip, fast-fail shedding, and half-open probe recovery.
          </p>
        </div>

        {/* State Badge */}
        <div className="flex flex-col items-start md:items-end">
          <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 tracking-wider mb-1">
            CIRCUIT BREAKER STATE
          </span>
          <div className={`flex items-center gap-3 px-4 py-2 border-2 ${currentVisual.border} ${currentVisual.bg}`}>
            <span className={`w-3 h-3 ${state === 'CLOSED' ? 'bg-emerald-500' : state === 'OPEN' ? 'bg-swiss-accent' : 'bg-amber-500'} rounded-none`} />
            <span className={`text-lg font-mono font-black uppercase tracking-wider ${currentVisual.text}`}>
              {state}
            </span>
          </div>
        </div>
      </div>

      {/* 3-State Machine Architecture Diagram */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className={`border-2 p-6 transition-all ${state === 'CLOSED' ? 'border-black bg-neutral-100 shadow-md ring-2 ring-black' : 'border-neutral-300 bg-white opacity-60'}`}>
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-black/20">
            <span className="text-xs font-mono font-bold uppercase">STATE 01</span>
            <span className="text-xs font-mono font-black text-emerald-600">CLOSED (HEALTHY)</span>
          </div>
          <p className="text-xs font-medium uppercase text-neutral-700 leading-relaxed mb-4">
            Passes 100% of event verification calls. Continuously tracks rolling error rate and consecutive failure streaks.
          </p>
          <div className="text-[10px] font-mono font-bold text-neutral-500 pt-2 border-t border-black/10">
            TRIP CONDITION: &gt; 5 FAILURES OR &gt; 50% ERROR RATE
          </div>
        </div>

        <div className={`border-2 p-6 transition-all ${state === 'OPEN' ? 'border-swiss-accent bg-black text-white shadow-md ring-2 ring-swiss-accent' : 'border-neutral-300 bg-white opacity-60'}`}>
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-white/20">
            <span className="text-xs font-mono font-bold uppercase text-neutral-400">STATE 02</span>
            <span className="text-xs font-mono font-black text-swiss-accent">OPEN (TRIPPED)</span>
          </div>
          <p className="text-xs font-medium uppercase text-neutral-300 leading-relaxed mb-4">
            Tripped state. Immediately fails fast with zero downstream HTTP requests, preventing server exhaustion.
          </p>
          <div className="text-[10px] font-mono font-bold text-neutral-400 pt-2 border-t border-white/10">
            COOLDOWN TIMER: 5.0 SECONDS
          </div>
        </div>

        <div className={`border-2 p-6 transition-all ${state === 'HALF_OPEN' ? 'border-amber-500 bg-amber-50 shadow-md ring-2 ring-amber-500' : 'border-neutral-300 bg-white opacity-60'}`}>
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-black/20">
            <span className="text-xs font-mono font-bold uppercase">STATE 03</span>
            <span className="text-xs font-mono font-black text-amber-600">HALF_OPEN (PROBE)</span>
          </div>
          <p className="text-xs font-medium uppercase text-neutral-700 leading-relaxed mb-4">
            Sends controlled trial requests to downstream. If successful, resets circuit to CLOSED; if any fail, re-trips to OPEN.
          </p>
          <div className="text-[10px] font-mono font-bold text-neutral-500 pt-2 border-t border-black/10">
            SUCCESS THRESHOLD: 3 CONSECUTIVE PASSES
          </div>
        </div>
      </div>

      {/* Telemetry & Live Chaos Control Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Circuit Breaker Telemetry (6 cols) */}
        <div className="lg:col-span-6 border-2 border-black p-6 bg-white">
          <div className="flex items-center justify-between pb-4 mb-6 border-b border-black/20">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-black">
              LIVE CIRCUIT TELEMETRY
            </span>
            <button
              onClick={handleResetCircuit}
              className="text-[11px] font-mono font-bold bg-neutral-100 hover:bg-black hover:text-white border border-black px-2 py-1 uppercase transition-all"
            >
              FORCE RESET
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="border border-black/20 p-4 bg-neutral-50">
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block mb-1">
                CONSECUTIVE FAILURES
              </span>
              <div className="text-2xl font-mono font-black text-black">
                {status?.consecutive_failures || 0} <span className="text-xs font-normal text-neutral-500">/ 5 max</span>
              </div>
            </div>

            <div className="border border-black/20 p-4 bg-neutral-50">
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block mb-1">
                FAILURE RATE
              </span>
              <div className="text-2xl font-mono font-black text-black">
                {((status?.failure_rate || 0) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="border border-black/20 p-4 bg-neutral-50">
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block mb-1">
                TOTAL REQUESTS
              </span>
              <div className="text-2xl font-mono font-black text-black">
                {status?.total_requests || 0}
              </div>
            </div>

            <div className="border border-black/20 p-4 bg-neutral-50">
              <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block mb-1">
                PROBE SUCCESSES
              </span>
              <div className="text-2xl font-mono font-black text-black">
                {status?.success_count || 0} <span className="text-xs font-normal text-neutral-500">/ 3 needed</span>
              </div>
            </div>
          </div>

          <p className="text-xs font-mono uppercase text-neutral-600">
            {currentVisual.desc}
          </p>
        </div>

        {/* Right: Downstream Fault Injection Controls (6 cols) */}
        <div className="lg:col-span-6 border-2 border-black p-6 bg-neutral-50 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-black/20">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-black">
                DOWNSTREAM FAULT INJECTION SUITE
              </span>
              <span className="text-[10px] font-mono bg-swiss-accent text-white px-2 py-0.5 font-bold uppercase">
                CHAOS ENGINE
              </span>
            </div>

            <div className="space-y-4 mb-6">
              {/* Failure Rate Slider */}
              <div>
                <div className="flex justify-between text-xs font-mono font-bold uppercase mb-1">
                  <span>500 ERROR INJECTION RATE:</span>
                  <span className="text-swiss-accent">{(failureRate * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={failureRate}
                  onChange={(e) => setFailureRate(parseFloat(e.target.value))}
                  className="w-full h-2 bg-neutral-200 border border-black accent-black cursor-pointer"
                />
              </div>

              {/* Rate Limit 429 Slider */}
              <div>
                <div className="flex justify-between text-xs font-mono font-bold uppercase mb-1">
                  <span>429 RATE LIMIT INJECTION RATE:</span>
                  <span className="text-amber-600">{(rateLimitRate * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={rateLimitRate}
                  onChange={(e) => setRateLimitRate(parseFloat(e.target.value))}
                  className="w-full h-2 bg-neutral-200 border border-black accent-black cursor-pointer"
                />
              </div>

              {/* Latency Injection */}
              <div>
                <div className="flex justify-between text-xs font-mono font-bold uppercase mb-1">
                  <span>DOWNSTREAM LATENCY SIMULATION:</span>
                  <span className="text-black font-black">{latencyMs} ms</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="2000"
                  step="50"
                  value={latencyMs}
                  onChange={(e) => setLatencyMs(parseInt(e.target.value))}
                  className="w-full h-2 bg-neutral-200 border border-black accent-black cursor-pointer"
                />
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <button
              onClick={handleUpdateFaults}
              disabled={isInjecting}
              className="w-full py-3 bg-black text-white hover:bg-swiss-accent font-mono text-xs font-black uppercase tracking-wider border-2 border-black transition-all cursor-pointer"
            >
              APPLY FAULT INJECTION TO DOWNSTREAM
            </button>

            <AnimatePresence>
              {feedback && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="p-2 bg-neutral-900 text-white text-center text-[10px] font-mono font-bold uppercase"
                >
                  {feedback}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
};
