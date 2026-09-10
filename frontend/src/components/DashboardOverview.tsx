import React from 'react';
import { Activity, CheckCircle2, Clock, Layers, AlertTriangle, ShieldCheck, ArrowUpRight } from 'lucide-react';
import { SystemMetrics } from '../types';

interface DashboardOverviewProps {
  metrics: SystemMetrics | null;
  isConnected: boolean;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ metrics, isConnected }) => {
  const m = metrics || {
    total_events: 0,
    events_per_second: 0,
    success_count: 0,
    failed_count: 0,
    retrying_count: 0,
    dlq_count: 0,
    duplicate_count: 0,
    success_rate: 100,
    queue_depth: 0,
    pending_events: 0,
    active_workers: 4,
    total_workers: 4,
    p50_latency_ms: 0,
    p95_latency_ms: 0,
    p99_latency_ms: 0,
    timestamp: new Date().toISOString()
  };

  return (
    <section id="monitoring" className="w-full border-t-4 border-black bg-white relative">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-16">
        {/* Section Header with Swiss Numbered Prefix */}
        <div className="border-b-4 border-black pb-6 mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 text-xs font-black uppercase tracking-widest text-[#FF3000]">
              <span>02. TELEMETRY</span>
              <span className="text-black">/</span>
              <span>LIVE PIPELINE OBSERVABILITY</span>
            </div>
            <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tighter text-black mt-2">
              System Telemetry
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <div className={`px-4 py-2 border-2 border-black font-mono text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${
              isConnected ? 'bg-black text-white' : 'bg-[#FF3000] text-white animate-pulse'
            }`}>
              <span className={`w-2 h-2 ${isConnected ? 'bg-[#FF3000]' : 'bg-white'}`} />
              {isConnected ? 'WS LIVE TELEMETRY STREAM' : 'WS RECONNECTING...'}
            </div>
          </div>
        </div>

        {/* 4-Column Primary Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border-4 border-black divide-y-4 sm:divide-y-0 sm:divide-x-4 divide-black bg-[#F2F2F2] swiss-grid-pattern">
          {/* Total Ingested */}
          <div className="p-8 bg-white hover:bg-[#F2F2F2] transition-colors duration-150 flex flex-col justify-between min-h-[190px]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-widest text-black">Total Ingested</span>
              <Activity className="w-4 h-4 text-black" />
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-black font-mono tracking-tighter text-black">
                {m.total_events.toLocaleString()}
              </div>
              <div className="text-xs font-mono font-bold uppercase text-black/70 mt-2 flex items-center gap-1">
                <span className="text-[#FF3000]">{m.events_per_second} REQ/S</span>
                <span>• 202 ACCEPTED</span>
              </div>
            </div>
          </div>

          {/* Success Rate */}
          <div className="p-8 bg-white hover:bg-[#F2F2F2] transition-colors duration-150 flex flex-col justify-between min-h-[190px]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-widest text-black">Success Rate</span>
              <CheckCircle2 className="w-4 h-4 text-black" />
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-black font-mono tracking-tighter text-black">
                {m.success_rate}%
              </div>
              <div className="text-xs font-mono font-bold uppercase text-black/70 mt-2">
                {m.success_count.toLocaleString()} VERIFIED COMMITS
              </div>
            </div>
          </div>

          {/* Queue Depth */}
          <div className="p-8 bg-white hover:bg-[#F2F2F2] transition-colors duration-150 flex flex-col justify-between min-h-[190px]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-widest text-black">Queue Depth</span>
              <Layers className="w-4 h-4 text-black" />
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-black font-mono tracking-tighter text-black">
                {m.queue_depth}
              </div>
              <div className="text-xs font-mono font-bold uppercase text-black/70 mt-2">
                {m.pending_events} IN CONSUMER PEL
              </div>
            </div>
          </div>

          {/* Dead Letter Queue */}
          <div className={`p-8 transition-colors duration-150 flex flex-col justify-between min-h-[190px] ${
            m.dlq_count > 0 ? 'bg-[#FF3000] text-white' : 'bg-white text-black hover:bg-[#F2F2F2]'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-widest">Dead Letter Queue</span>
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-black font-mono tracking-tighter">
                {m.dlq_count}
              </div>
              <div className="text-xs font-mono font-bold uppercase opacity-90 mt-2">
                {m.retrying_count} IN BACKOFF RETRY
              </div>
            </div>
          </div>
        </div>

        {/* Latency Percentiles & Fleet Bar (Asymmetric 8:4 Grid) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 border-4 border-black border-t-0 bg-white">
          {/* Latency Percentiles (8 Cols) */}
          <div className="lg:col-span-8 p-8 border-b-4 lg:border-b-0 lg:border-r-4 border-black bg-[#F2F2F2] swiss-dots">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-black" />
                <span className="text-xs font-black uppercase tracking-widest text-black">
                  End-to-End Latency Percentiles
                </span>
              </div>
              <span className="text-xs font-mono font-bold text-[#FF3000] uppercase">
                Rolling 500 Samples
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white border-2 border-black p-5 text-left">
                <div className="text-[11px] font-black uppercase tracking-wider text-black/60">P50 (Median)</div>
                <div className="text-3xl sm:text-4xl font-black font-mono text-black mt-2">{m.p50_latency_ms} <span className="text-xs font-normal">ms</span></div>
              </div>
              <div className="bg-white border-2 border-black p-5 text-left">
                <div className="text-[11px] font-black uppercase tracking-wider text-black/60">P95 Latency</div>
                <div className="text-3xl sm:text-4xl font-black font-mono text-black mt-2">{m.p95_latency_ms} <span className="text-xs font-normal">ms</span></div>
              </div>
              <div className="bg-white border-2 border-black p-5 text-left border-l-4 border-l-[#FF3000]">
                <div className="text-[11px] font-black uppercase tracking-wider text-[#FF3000]">P99 Tail</div>
                <div className="text-3xl sm:text-4xl font-black font-mono text-black mt-2">{m.p99_latency_ms} <span className="text-xs font-normal">ms</span></div>
              </div>
            </div>
          </div>

          {/* Idempotency & Fleet Metrics (4 Cols) */}
          <div className="lg:col-span-4 p-8 bg-white flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-6">
                <span className="text-xs font-black uppercase tracking-widest text-black flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#FF3000]" />
                  Defense & Workers
                </span>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b-2 border-black text-sm">
                  <span className="font-bold uppercase tracking-tight">Duplicate Hits Intercepted:</span>
                  <span className="font-mono font-black text-lg bg-black text-white px-2 py-0.5">
                    {m.duplicate_count}
                  </span>
                </div>
                <div className="flex items-center justify-between pb-3 border-b-2 border-black text-sm">
                  <span className="font-bold uppercase tracking-tight">Active Worker Threads:</span>
                  <span className="font-mono font-black text-lg text-black">
                    {m.active_workers} / {m.total_workers}
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-6 text-[11px] font-mono uppercase font-bold text-black/70 flex items-center justify-between">
              <span>Ingestion Budget: &lt;10ms</span>
              <span className="text-[#FF3000]">100% Zero-Loss ACK</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
