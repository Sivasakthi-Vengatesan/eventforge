import React from 'react';
import { Shield, Database, Cpu, Radio, RotateCcw, AlertOctagon, Activity, Plus } from 'lucide-react';

interface ArchitectureViewProps {
  selectedServices: string[];
  onSelectService: (service: string) => void;
}

export const ArchitectureView: React.FC<ArchitectureViewProps> = ({ selectedServices, onSelectService }) => {
  const components = [
    {
      num: "01",
      name: "Webhook Gateway",
      tag: "Ingestion & Security",
      icon: Shield,
      desc: "Instant HMAC-SHA256 signature verification & timestamp replay window checks before returning HTTP 202 in <10ms.",
      details: "POST /api/v1/webhooks/{provider} • Constant-time comparison",
    },
    {
      num: "02",
      name: "Redis Streams",
      tag: "Message Queue",
      icon: Radio,
      desc: "Distributed event stream using Consumer Groups ('event-workers') with Pending Entries List (PEL) to prevent lost messages.",
      details: "Stream: events:incoming • XADD / XREADGROUP / XACK / XAUTOCLAIM",
    },
    {
      num: "03",
      name: "Worker Pool",
      tag: "Async Concurrency",
      icon: Cpu,
      desc: "Scalable asynchronous worker fleet consuming batches from Redis Streams and executing third-party verifications with backpressure.",
      details: "Configurable concurrency • Independent worker heartbeats",
    },
    {
      num: "04",
      name: "PostgreSQL",
      tag: "ACID Storage",
      icon: Database,
      desc: "Primary source of truth storing event states, detailed attempt logs, and enforcing atomic uniqueness on (provider, event_id).",
      details: "Unique constraints • JSON payload storage • Indexed status",
    },
    {
      num: "05",
      name: "Retry Engine",
      tag: "Resilience",
      icon: RotateCcw,
      desc: "Classifies failures (500, 429, timeout) and calculates exponential backoff with full randomized jitter to prevent thundering herds.",
      details: "delay = base × 2^attempt + jitter • Max retries = 5",
    },
    {
      num: "06",
      name: "Dead Letter Queue",
      tag: "Fault Isolation",
      icon: AlertOctagon,
      desc: "Safely quarantines events exceeding retry limits or fatal errors. Enables operator inspection, payload modification, and replay.",
      details: "POST /api/v1/dlq/:id/retry • Stack trace recording",
    },
    {
      num: "07",
      name: "Monitoring",
      tag: "Observability",
      icon: Activity,
      desc: "Real-time WebSocket hub pushing state transitions, throughput counters, and rolling P50/P95/P99 latency percentiles.",
      details: "WebSocket /ws/monitor • Zero-polling live metrics",
    },
  ];

  return (
    <section id="architecture" className="w-full border-t-4 border-black bg-white relative">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-16">
        {/* Section Header */}
        <div className="border-b-4 border-black pb-6 mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 text-xs font-black uppercase tracking-widest text-[#FF3000]">
              <span>01. ARCHITECTURE</span>
              <span className="text-black">/</span>
              <span>SYSTEM DESIGN SPECIFICATION</span>
            </div>
            <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tighter text-black mt-2">
              Pipeline Topology
            </h2>
          </div>
          <p className="text-sm font-medium text-black/70 max-w-md">
            Click any component to toggle its inspection state in the grid. Selected components are highlighted with high-contrast signal inversions.
          </p>
        </div>

        {/* Swiss Grid of Architecture Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-4 border-black bg-[#F2F2F2] swiss-diagonal gap-1">
          {components.map((comp) => {
            const isSelected = selectedServices.includes(comp.name);
            const IconComponent = comp.icon;
            return (
              <div
                key={comp.name}
                onClick={() => onSelectService(comp.name)}
                className={`p-8 transition-colors duration-150 cursor-pointer flex flex-col justify-between min-h-[300px] select-none ${
                  isSelected
                    ? 'bg-black text-white'
                    : 'bg-white text-black hover:bg-[#F2F2F2]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between pb-4 border-b-2 border-current mb-6">
                    <div className="flex items-center gap-2">
                      <span className={`font-mono text-sm font-black ${isSelected ? 'text-[#FF3000]' : 'text-black'}`}>
                        {comp.num}.
                      </span>
                      <span className="text-[11px] font-black uppercase tracking-widest opacity-80">
                        {comp.tag}
                      </span>
                    </div>
                    <IconComponent className={`w-5 h-5 ${isSelected ? 'text-[#FF3000]' : 'text-black'}`} />
                  </div>

                  <h3 className="text-2xl font-black uppercase tracking-tight mb-3">
                    {comp.name}
                  </h3>
                  <p className={`text-xs sm:text-sm leading-relaxed ${isSelected ? 'text-neutral-300' : 'text-neutral-700'}`}>
                    {comp.desc}
                  </p>
                </div>

                <div className={`mt-8 pt-4 border-t-2 border-current text-[11px] font-mono font-bold uppercase ${
                  isSelected ? 'text-[#FF3000]' : 'text-black/60'
                }`}>
                  {comp.details}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
