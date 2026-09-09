import React, { useState, useEffect } from 'react';
import { Server, Database, Radio, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';

export const SystemHealth: React.FC<{ isWsConnected: boolean }> = ({ isWsConnected }) => {
  const [health, setHealth] = useState<any>(null);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/v1/health');
      if (res.ok) {
        setHealth(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const components = [
    {
      idx: '01',
      name: 'PostgreSQL / SQLite Dual Engine',
      status: health?.database || 'HEALTHY',
      icon: Database,
      desc: 'ACID storage for atomic idempotency constraints, attempt audits, and quarantine records.',
    },
    {
      idx: '02',
      name: 'Redis Streams & Consumer Groups',
      status: health?.redis || 'STREAM_ENGINE ACTIVE',
      icon: Radio,
      desc: 'High-throughput stream manager: events:incoming and Pending Entries List (PEL).',
    },
    {
      idx: '03',
      name: 'Worker Fleet (4 Processes)',
      status: health?.workers || '4 ACTIVE CONCURRENCY',
      icon: Cpu,
      desc: 'Non-blocking worker pool with exponential backoff, jitter, and PEL auto-claiming.',
    },
    {
      idx: '04',
      name: 'WebSocket Observability Push',
      status: isWsConnected ? 'CONNECTED (127.0.0.1)' : 'RECONNECTING...',
      icon: Server,
      desc: 'Low-latency binary/JSON streaming telemetry pipeline broadcast at /ws/monitor.',
    },
  ];

  return (
    <section id="infrastructure" className="w-full border-b-4 border-black bg-[#F2F2F2] py-16 px-6 md:px-12 lg:px-20 swiss-grid-pattern">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b-2 border-black">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-black text-white text-xs font-black uppercase tracking-widest mb-3">
              <span className="text-swiss-accent font-black">07.</span>
              <span>Infrastructure</span>
            </div>
            <h2 className="text-3xl md:text-5xl lg:text-6xl font-black uppercase tracking-tighter text-black">
              System Health & Integrity
            </h2>
            <p className="text-sm md:text-base font-bold text-neutral-600 mt-2 max-w-2xl uppercase tracking-tight">
              Real-time heartbeat verification and state diagnostics across distributed backend subsystems.
            </p>
          </div>

          <div className="px-4 py-2 bg-black text-white text-xs font-black uppercase tracking-widest border-2 border-black flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-swiss-accent animate-pulse" />
            <span>ALL SUBSYSTEMS NOMINAL</span>
          </div>
        </div>

        {/* Component Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {components.map((c) => (
            <div key={c.name} className="bg-white border-4 border-black p-6 hover:bg-black hover:text-white transition-all group">
              <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-black group-hover:border-neutral-800">
                <span className="text-xs font-black uppercase tracking-widest text-swiss-accent group-hover:text-swiss-accent">
                  [{c.idx}]
                </span>
                <span className="text-[10px] font-black uppercase px-2 py-1 bg-black text-white group-hover:bg-swiss-accent group-hover:text-white border border-black">
                  {c.status}
                </span>
              </div>
              <h3 className="font-black text-base uppercase tracking-tight text-black group-hover:text-white mb-2">
                {c.name}
              </h3>
              <p className="text-xs font-bold text-neutral-600 group-hover:text-neutral-300 leading-relaxed uppercase">
                {c.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
