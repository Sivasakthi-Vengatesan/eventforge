import React, { useState, useEffect } from 'react';
import { AlertOctagon, RotateCcw, Trash2, CheckCircle2, RefreshCw, AlertTriangle } from 'lucide-react';
import { DLQItem } from '../types';
import { fetchDLQ, retryDLQ, deleteDLQ } from '../lib/api';
import { formatTimestamp } from '../lib/utils';

export const DLQManager: React.FC = () => {
  const [items, setItems] = useState<DLQItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadDLQ = async () => {
    setLoading(true);
    try {
      const data = await fetchDLQ();
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDLQ();
    const interval = setInterval(loadDLQ, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleRetry = async (dlqId: string) => {
    try {
      await retryDLQ(dlqId);
      setStatusMsg(`EVENT [${dlqId}] RE-ENQUEUED TO STREAM`);
      setTimeout(() => setStatusMsg(null), 3500);
      loadDLQ();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (dlqId: string) => {
    try {
      await deleteDLQ(dlqId);
      setStatusMsg(`EVENT [${dlqId}] PERMANENTLY PURGED`);
      setTimeout(() => setStatusMsg(null), 3500);
      loadDLQ();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <section id="dlq" className="w-full border-b-4 border-black bg-white py-16 px-6 md:px-12 lg:px-20">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b-2 border-black">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-black text-white text-xs font-black uppercase tracking-widest mb-3">
              <span className="text-swiss-accent font-black">05.</span>
              <span>Fault Isolation</span>
            </div>
            <h2 className="text-3xl md:text-5xl lg:text-6xl font-black uppercase tracking-tighter text-black">
              Dead Letter Queue
            </h2>
            <p className="text-sm md:text-base font-bold text-neutral-600 mt-2 max-w-2xl uppercase tracking-tight">
              Quarantine repository for poisoned events exceeding MAX_RETRIES (5) or failing structural invariants.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {statusMsg && (
              <span className="text-xs font-black uppercase tracking-wider bg-swiss-accent text-white px-3 py-2 border-2 border-black animate-pulse">
                {statusMsg}
              </span>
            )}
            <div className="px-4 py-2 border-2 border-black bg-[#F2F2F2] text-xs font-black uppercase tracking-wider flex items-center gap-2">
              <span>QUARANTINE COUNT:</span>
              <span className={`font-mono text-sm ${total > 0 ? 'text-swiss-accent' : 'text-black'}`}>{total}</span>
            </div>
            <button
              onClick={loadDLQ}
              className="px-4 py-2 bg-black text-white hover:bg-swiss-accent hover:text-white border-2 border-black text-xs font-black uppercase tracking-widest transition-colors flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Table Container */}
        <div className="border-4 border-black bg-white overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-bold">
              <thead className="bg-black text-white text-xs uppercase tracking-widest">
                <tr>
                  <th className="py-4 px-4 border-r border-neutral-800">DLQ Identifier</th>
                  <th className="py-4 px-4 border-r border-neutral-800">Original Event ID</th>
                  <th className="py-4 px-4 border-r border-neutral-800">Provider</th>
                  <th className="py-4 px-4 border-r border-neutral-800">Failure Diagnostics</th>
                  <th className="py-4 px-4 border-r border-neutral-800 text-center">Attempts</th>
                  <th className="py-4 px-4 border-r border-neutral-800">Timestamp</th>
                  <th className="py-4 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-black">
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-16 text-center bg-[#F2F2F2] swiss-dots">
                      <div className="flex flex-col items-center justify-center gap-3">
                        <CheckCircle2 className="w-10 h-10 text-black" />
                        <span className="font-black text-sm uppercase tracking-widest text-black">
                          Dead Letter Queue Empty — All Ingested Events Reconciled
                        </span>
                        <p className="text-xs text-neutral-600 uppercase font-semibold">
                          Zero poison pills currently active in quarantine storage.
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.id} className="hover:bg-neutral-100 transition-colors group">
                      <td className="py-3.5 px-4 font-mono font-black text-swiss-accent border-r-2 border-black">
                        {item.dlq_id}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-black border-r-2 border-black">
                        {item.event_id}
                      </td>
                      <td className="py-3.5 px-4 uppercase font-black text-black border-r-2 border-black">
                        {item.provider}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-black border-r-2 border-black max-w-xs truncate">
                        <span className="bg-rose-100 text-rose-900 px-1 py-0.5 border border-rose-300">
                          {item.failure_reason}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-center font-black text-black border-r-2 border-black">
                        {item.retry_count}
                      </td>
                      <td className="py-3.5 px-4 text-neutral-700 font-mono text-xs border-r-2 border-black">
                        {formatTimestamp(item.created_at)}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleRetry(item.dlq_id)}
                            className="px-3 py-1.5 bg-black hover:bg-swiss-accent text-white text-xs font-black uppercase tracking-wider transition-colors flex items-center gap-1.5 border border-black"
                            title="Re-enqueue payload to Redis Stream"
                          >
                            <RotateCcw className="w-3 h-3" />
                            <span>Replay</span>
                          </button>
                          <button
                            onClick={() => handleDelete(item.dlq_id)}
                            className="p-1.5 bg-[#F2F2F2] hover:bg-black hover:text-white text-black border border-black transition-colors"
                            title="Purge record"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
};
