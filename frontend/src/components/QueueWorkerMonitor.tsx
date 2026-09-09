import React, { useState, useEffect } from 'react';
import { Cpu, RefreshCw, AlertCircle, Play, Square, Activity } from 'lucide-react';
import { WorkerItem } from '../types';
import { fetchWorkers, restartWorker, killWorker } from '../lib/api';
import { formatTimestamp, getStatusBadgeClass } from '../lib/utils';

interface QueueWorkerMonitorProps {
  queueDepth: number;
  pendingCount: number;
}

export const QueueWorkerMonitor: React.FC<QueueWorkerMonitorProps> = ({ queueDepth, pendingCount }) => {
  const [workers, setWorkers] = useState<WorkerItem[]>([]);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadWorkers = async () => {
    try {
      const data = await fetchWorkers();
      setWorkers(data);
    } catch (e) {
      console.error('Failed to load workers', e);
    }
  };

  useEffect(() => {
    loadWorkers();
    const interval = setInterval(loadWorkers, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleRestart = async (id: string) => {
    try {
      await restartWorker(id);
      setActionMessage(`Worker ${id} restarted`);
      setTimeout(() => setActionMessage(null), 3000);
      loadWorkers();
    } catch (e) {
      console.error(e);
    }
  };

  const handleKill = async (id: string) => {
    try {
      await killWorker(id);
      setActionMessage(`Simulated crash for ${id}! PEL unacknowledged messages will be claimed.`);
      setTimeout(() => setActionMessage(null), 4000);
      loadWorkers();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <section id="workers" className="w-full border-t-4 border-black bg-white relative">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-16">
        {/* Section Header */}
        <div className="border-b-4 border-black pb-6 mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 text-xs font-black uppercase tracking-widest text-[#FF3000]">
              <span>03. CONCURRENCY</span>
              <span className="text-black">/</span>
              <span>ASYNC WORKER FLEET & REDIS PEL</span>
            </div>
            <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tighter text-black mt-2">
              Queue & Workers
            </h2>
          </div>

          {actionMessage && (
            <div className="bg-[#FF3000] text-white text-xs font-mono font-bold uppercase px-4 py-2 border-2 border-black flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{actionMessage}</span>
            </div>
          )}
        </div>

        {/* Redis Stream Status Grid Banner */}
        <div className="border-4 border-black bg-black text-white p-6 sm:p-8 mb-8 grid grid-cols-1 sm:grid-cols-3 gap-6 font-mono">
          <div>
            <div className="text-[11px] font-black uppercase tracking-widest text-[#FF3000]">Stream Identifier</div>
            <div className="text-lg font-bold mt-1">events:incoming</div>
            <div className="text-[11px] text-white/60 mt-0.5">Group: event-workers</div>
          </div>
          <div className="border-t-2 sm:border-t-0 sm:border-l-2 border-white/20 sm:pl-6 pt-4 sm:pt-0">
            <div className="text-[11px] font-black uppercase tracking-widest text-white/80">Stream Length (XLEN)</div>
            <div className="text-3xl font-black text-white mt-1">{queueDepth}</div>
          </div>
          <div className="border-t-2 sm:border-t-0 sm:border-l-2 border-white/20 sm:pl-6 pt-4 sm:pt-0">
            <div className="text-[11px] font-black uppercase tracking-widest text-[#FF3000]">Pending Unacknowledged (PEL)</div>
            <div className="text-3xl font-black text-[#FF3000] mt-1">{pendingCount}</div>
          </div>
        </div>

        {/* Workers Fleet Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 border-4 border-black divide-y-4 md:divide-y-0 md:divide-x-4 divide-black bg-[#F2F2F2] swiss-grid-pattern">
          {workers.map((w) => (
            <div
              key={w.id}
              className="p-6 bg-white hover:bg-[#F2F2F2] transition-colors duration-150 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between pb-3 border-b-2 border-black mb-4">
                  <span className="font-mono font-black text-base text-black uppercase">{w.id}</span>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 ${getStatusBadgeClass(w.status)}`}>
                    {w.status}
                  </span>
                </div>

                {w.current_event_id ? (
                  <div className="bg-[#FF3000] text-white p-3 mb-4 font-mono text-xs border-2 border-black">
                    <div className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 animate-spin" />
                      <span>Processing Event:</span>
                    </div>
                    <div className="text-[11px] font-bold truncate mt-1">{w.current_event_id}</div>
                    <div className="text-[10px] uppercase opacity-90 mt-0.5">{w.current_event_provider} • {w.current_event_type}</div>
                  </div>
                ) : (
                  <div className="bg-[#F2F2F2] border-2 border-black/20 p-3 mb-4 text-xs font-mono text-black/50 italic">
                    Awaiting next batch from stream...
                  </div>
                )}

                <div className="space-y-2 text-xs font-mono text-black">
                  <div className="flex justify-between pb-1 border-b border-black/10">
                    <span className="text-black/60 uppercase">Total Completed:</span>
                    <span className="font-bold">{w.processed_count}</span>
                  </div>
                  <div className="flex justify-between pb-1 border-b border-black/10">
                    <span className="text-black/60 uppercase">Success / Fail:</span>
                    <span className="font-bold">{w.success_count} / <span className="text-[#FF3000]">{w.failure_count}</span></span>
                  </div>
                  <div className="flex justify-between pb-1 border-b border-black/10">
                    <span className="text-black/60 uppercase">Avg Latency:</span>
                    <span className="font-bold">{w.average_duration_ms} ms</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-black/50 pt-1">
                    <span>Heartbeat:</span>
                    <span>{formatTimestamp(w.last_heartbeat)}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 pt-4 border-t-2 border-black grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleRestart(w.id)}
                  className="py-2 px-3 bg-black hover:bg-[#FF3000] text-white text-xs font-mono font-bold uppercase transition-colors duration-150 flex items-center justify-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Restart</span>
                </button>
                <button
                  onClick={() => handleKill(w.id)}
                  className="py-2 px-3 bg-white hover:bg-black hover:text-white text-black border-2 border-black text-xs font-mono font-bold uppercase transition-colors duration-150 flex items-center justify-center gap-1"
                >
                  <Square className="w-3 h-3 fill-current" />
                  <span>Kill</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
