import React, { useState } from 'react';
import { Play, Zap, ShieldAlert, Copy, RefreshCw, AlertTriangle, CheckCircle2, Terminal } from 'lucide-react';
import { ingestSampleWebhook } from '../lib/api';

export const LiveGenerator: React.FC = () => {
  const [running, setRunning] = useState(false);
  const [logMessages, setLogMessages] = useState<string[]>([]);
  const [customCount, setCustomCount] = useState(25);

  const appendLog = (msg: string) => {
    setLogMessages((prev) => [ `[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 25) ]);
  };

  const runBurst = async (provider: string, count: number, fault?: string, duplicateSameId = false) => {
    setRunning(true);
    appendLog(`LAUNCHING BURST: ${count} ${provider.toUpperCase()} EVENTS ${fault ? `(FAULT: ${fault})` : ''}...`);
    
    const sharedId = `evt_dup_${Math.random().toString(36).substring(2, 9)}`;

    for (let i = 0; i < count; i++) {
      const eventId = duplicateSameId ? sharedId : `evt_${provider.slice(0, 3)}_${Math.random().toString(36).substring(2, 10)}`;
      const payload = {
        id: eventId,
        type: provider === 'stripe' ? 'payment_intent.succeeded' : provider === 'razorpay' ? 'payment.captured' : 'push',
        data: { amount: Math.floor(Math.random() * 20000) + 1000, currency: 'usd' },
        ...(fault ? { force_fault: fault } : {})
      };

      try {
        const res = await ingestSampleWebhook(provider, payload, fault ? { 'x-mock-fault': fault } : {});
        if (i === 0 || i === count - 1 || res.status === 'DUPLICATE') {
          appendLog(`-> [${res.status}] ${res.event_id} (${res.message || 'STREAM_COMMITTED'})`);
        }
      } catch (err: any) {
        appendLog(`-> [ERROR] ${err.message}`);
      }
      
      if (i % 5 === 0) await new Promise((r) => setTimeout(r, 20));
    }

    appendLog(`[COMPLETE] Burst of ${count} events dispatched.`);
    setRunning(false);
  };

  const testInvalidSignature = async () => {
    setRunning(true);
    appendLog('TRANSMITTING PAYLOAD WITH FORGED HMAC SIGNATURE...');
    try {
      const res = await fetch('/api/v1/webhooks/stripe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Stripe-Signature': 't=1700000000,v1=forged_invalid_signature_hash_00000'
        },
        body: JSON.stringify({ id: 'evt_forged_123', type: 'payment_intent.succeeded' })
      });
      if (res.status === 401 || res.status === 403) {
        appendLog(`[DEFENSE_ENGAGED] HTTP ${res.status} FORBIDDEN — INVALID HMAC SIGNATURE REJECTED.`);
      } else {
        appendLog(`RESPONSE: HTTP ${res.status}`);
      }
    } catch (e: any) {
      appendLog(`ERROR: ${e.message}`);
    }
    setRunning(false);
  };

  return (
    <section id="generator" className="w-full border-b-4 border-black bg-white py-16 px-6 md:px-12 lg:px-20">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b-2 border-black">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-black text-white text-xs font-black uppercase tracking-widest mb-3">
              <span className="text-swiss-accent font-black">06.</span>
              <span>Simulation & Load Suite</span>
            </div>
            <h2 className="text-3xl md:text-5xl lg:text-6xl font-black uppercase tracking-tighter text-black">
              Traffic & Fault Generator
            </h2>
            <p className="text-sm md:text-base font-bold text-neutral-600 mt-2 max-w-2xl uppercase tracking-tight">
              Inject production-scale event bursts, simulate downstream HTTP 500 crashes, force idempotency storms, and test HMAC verification.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 border border-black ${running ? 'bg-swiss-accent animate-ping' : 'bg-black'}`} />
            <span className="text-xs font-black uppercase tracking-widest text-black">
              {running ? 'TRANSMITTING STREAM...' : 'SYSTEM READY'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Action Trigger Matrix */}
          <div className="lg:col-span-7 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Action 1: Stripe Burst */}
              <button
                onClick={() => runBurst('stripe', 25)}
                disabled={running}
                className="p-5 bg-white border-2 border-black hover:bg-black hover:text-white text-left transition-all group disabled:opacity-50 relative overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black uppercase tracking-widest text-swiss-accent group-hover:text-white">
                    01 // STRIPE
                  </span>
                  <span className="text-black group-hover:text-white font-black">→</span>
                </div>
                <div className="font-black text-sm uppercase tracking-tight text-black group-hover:text-white">
                  Burst 25 Stripe Events
                </div>
                <p className="text-xs font-bold text-neutral-500 group-hover:text-neutral-300 mt-1 uppercase leading-snug">
                  Dispatches 25 concurrent webhook payloads into the Redis Stream pipeline.
                </p>
              </button>

              {/* Action 2: Razorpay Burst */}
              <button
                onClick={() => runBurst('razorpay', 30)}
                disabled={running}
                className="p-5 bg-white border-2 border-black hover:bg-black hover:text-white text-left transition-all group disabled:opacity-50 relative overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black uppercase tracking-widest text-swiss-accent group-hover:text-white">
                    02 // RAZORPAY
                  </span>
                  <span className="text-black group-hover:text-white font-black">→</span>
                </div>
                <div className="font-black text-sm uppercase tracking-tight text-black group-hover:text-white">
                  Burst 30 Razorpay Events
                </div>
                <p className="text-xs font-bold text-neutral-500 group-hover:text-neutral-300 mt-1 uppercase leading-snug">
                  Tests multi-provider concurrent streaming across 4 consumer workers.
                </p>
              </button>

              {/* Action 3: Duplicate Storm */}
              <button
                onClick={() => runBurst('stripe', 10, undefined, true)}
                disabled={running}
                className="p-5 bg-white border-2 border-black hover:bg-black hover:text-white text-left transition-all group disabled:opacity-50 relative overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black uppercase tracking-widest text-swiss-accent group-hover:text-white">
                    03 // IDEMPOTENCY
                  </span>
                  <span className="text-black group-hover:text-white font-black">→</span>
                </div>
                <div className="font-black text-sm uppercase tracking-tight text-black group-hover:text-white">
                  10x Duplicate Storm
                </div>
                <p className="text-xs font-bold text-neutral-500 group-hover:text-neutral-300 mt-1 uppercase leading-snug">
                  Sends 10 identical IDs: 1 accepted, 9 flagged as DUPLICATE instantly.
                </p>
              </button>

              {/* Action 4: Inject 500s */}
              <button
                onClick={() => runBurst('stripe', 5, '500')}
                disabled={running}
                className="p-5 bg-white border-2 border-black hover:bg-black hover:text-white text-left transition-all group disabled:opacity-50 relative overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black uppercase tracking-widest text-swiss-accent group-hover:text-white">
                    04 // RETRY ENGINE
                  </span>
                  <span className="text-black group-hover:text-white font-black">→</span>
                </div>
                <div className="font-black text-sm uppercase tracking-tight text-black group-hover:text-white">
                  Inject Downstream 500s
                </div>
                <p className="text-xs font-bold text-neutral-500 group-hover:text-neutral-300 mt-1 uppercase leading-snug">
                  Triggers exponential backoff + full jitter retry schedule across workers.
                </p>
              </button>

              {/* Action 5: Tampered HMAC */}
              <button
                onClick={testInvalidSignature}
                disabled={running}
                className="p-5 bg-white border-2 border-black hover:bg-swiss-accent hover:text-white text-left transition-all group disabled:opacity-50 relative overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black uppercase tracking-widest text-black group-hover:text-white">
                    05 // SECURITY
                  </span>
                  <span className="text-black group-hover:text-white font-black">→</span>
                </div>
                <div className="font-black text-sm uppercase tracking-tight text-black group-hover:text-white">
                  Forge Tampered HMAC
                </div>
                <p className="text-xs font-bold text-neutral-500 group-hover:text-white mt-1 uppercase leading-snug">
                  Verifies perimeter HMAC-SHA256 rejection before touching the stream.
                </p>
              </button>

              {/* Action 6: DLQ Poison Pill */}
              <button
                onClick={() => runBurst('stripe', 2, 'invalid_data')}
                disabled={running}
                className="p-5 bg-white border-2 border-black hover:bg-swiss-accent hover:text-white text-left transition-all group disabled:opacity-50 relative overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black uppercase tracking-widest text-black group-hover:text-white">
                    06 // DLQ POISON
                  </span>
                  <span className="text-black group-hover:text-white font-black">→</span>
                </div>
                <div className="font-black text-sm uppercase tracking-tight text-black group-hover:text-white">
                  Trigger DLQ Transition
                </div>
                <p className="text-xs font-bold text-neutral-500 group-hover:text-white mt-1 uppercase leading-snug">
                  Injects non-retryable schema error to isolate event directly in DLQ.
                </p>
              </button>
            </div>

            {/* Custom Load Configurator */}
            <div className="p-6 border-4 border-black bg-[#F2F2F2] flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4 w-full sm:w-auto">
                <span className="text-xs font-black uppercase tracking-wider text-black">
                  Custom Batch Scale:
                </span>
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={customCount}
                  onChange={(e) => setCustomCount(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-24 px-3 py-2 bg-white border-2 border-black text-xs font-mono font-black text-center focus:outline-none focus:border-swiss-accent"
                />
                <span className="text-xs font-bold text-neutral-600 uppercase">Events</span>
              </div>
              <button
                onClick={() => runBurst('stripe', customCount)}
                disabled={running}
                className="w-full sm:w-auto px-8 py-3 bg-black hover:bg-swiss-accent text-white text-xs font-black uppercase tracking-widest border-2 border-black transition-colors disabled:opacity-50"
              >
                {running ? 'STREAMING...' : `EXECUTE ${customCount} EVENTS`}
              </button>
            </div>
          </div>

          {/* Monospace Output Terminal */}
          <div className="lg:col-span-5 border-4 border-black bg-black text-white p-6 flex flex-col justify-between h-96 lg:h-auto font-mono text-xs shadow-none">
            <div className="flex items-center justify-between pb-4 border-b-2 border-neutral-800 text-[11px]">
              <span className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-swiss-accent" />
                <span className="font-black tracking-widest uppercase">GENERATOR_OUTPUT.LOG</span>
              </span>
              <button
                onClick={() => setLogMessages([])}
                className="text-neutral-400 hover:text-white uppercase font-bold text-[10px]"
              >
                [CLEAR]
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-2 text-[11px] select-text">
              {logMessages.length === 0 ? (
                <div className="text-neutral-500 italic uppercase">
                  &gt; STANDBY: CLICK ANY TRIGGER MATRIX BUTTON TO COMMENCE LIVE STREAM TEST...
                </div>
              ) : (
                logMessages.map((msg, i) => (
                  <div key={i} className={`leading-relaxed ${msg.includes('ERROR') || msg.includes('FORBIDDEN') ? 'text-swiss-accent font-bold' : msg.includes('COMPLETE') ? 'text-white font-bold' : 'text-neutral-300'}`}>
                    {msg}
                  </div>
                ))
              )}
            </div>

            <div className="pt-3 border-t-2 border-neutral-800 text-[10px] text-neutral-400 flex justify-between font-bold uppercase tracking-wider">
              <span>DRIVER: ASYNC HTTPX</span>
              <span>ENDPOINT: /API/V1/WEBHOOKS</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
