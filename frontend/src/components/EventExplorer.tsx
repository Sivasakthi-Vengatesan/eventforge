import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, X, ChevronRight, Clock, ShieldCheck, Database } from 'lucide-react';
import { EventItem, EventDetailItem } from '../types';
import { fetchEvents, fetchEventDetail } from '../lib/api';
import { formatTimestamp, getStatusBadgeClass } from '../lib/utils';

export const EventExplorer: React.FC = () => {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedEvent, setSelectedEvent] = useState<EventDetailItem | null>(null);
  const [loading, setLoading] = useState(false);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await fetchEvents({
        search: search || undefined,
        provider: selectedProvider || undefined,
        status: selectedStatus || undefined,
        page_size: 50,
      });
      setEvents(data.items);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
    const interval = setInterval(loadEvents, 3000);
    return () => clearInterval(interval);
  }, [search, selectedProvider, selectedStatus]);

  const handleInspect = async (eventId: string) => {
    try {
      const detail = await fetchEventDetail(eventId);
      setSelectedEvent(detail);
    } catch (e) {
      console.error(e);
    }
  };

  const statuses = ['', 'QUEUED', 'PROCESSING', 'SUCCESS', 'RETRYING', 'FAILED', 'DLQ', 'DUPLICATE'];
  const providers = ['', 'stripe', 'razorpay', 'github', 'generic'];

  return (
    <section id="events" className="w-full border-t-4 border-black bg-white relative">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-16">
        {/* Section Header */}
        <div className="border-b-4 border-black pb-6 mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 text-xs font-black uppercase tracking-widest text-[#FF3000]">
              <span>04. AUDIT TRAIL</span>
              <span className="text-black">/</span>
              <span>EVENT STREAM & ATTEMPTS LOG</span>
            </div>
            <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tighter text-black mt-2">
              Event Stream
            </h2>
          </div>

          <button
            onClick={loadEvents}
            className="px-6 py-3 bg-black hover:bg-[#FF3000] text-white text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-2 transition-colors duration-150"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Table ({total} Total)</span>
          </button>
        </div>

        {/* Filter Controls Bar */}
        <div className="border-4 border-black bg-[#F2F2F2] p-4 sm:p-6 mb-8 flex flex-col lg:flex-row gap-4 items-stretch lg:items-center justify-between">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-black" />
            <input
              type="text"
              placeholder="SEARCH EVENT ID (EX: EVT_STR_...)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-white border-2 border-black text-xs sm:text-sm font-mono font-bold uppercase placeholder:text-black/40 focus:outline-none focus:border-[#FF3000]"
            />
          </div>

          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="bg-white border-2 border-black px-4 py-3 text-xs sm:text-sm font-mono font-bold uppercase focus:outline-none focus:border-[#FF3000]"
          >
            <option value="">ALL PROVIDERS</option>
            <option value="stripe">STRIPE</option>
            <option value="razorpay">RAZORPAY</option>
            <option value="github">GITHUB</option>
            <option value="generic">GENERIC</option>
          </select>

          {/* Status Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto">
            {statuses.map((st) => (
              <button
                key={st || 'all'}
                onClick={() => setSelectedStatus(st)}
                className={`px-3 py-2 text-xs font-mono font-bold uppercase whitespace-nowrap transition-colors duration-150 border-2 border-black ${
                  selectedStatus === st
                    ? 'bg-black text-white'
                    : 'bg-white text-black hover:bg-[#FF3000] hover:text-white'
                }`}
              >
                {st || 'ALL'}
              </button>
            ))}
          </div>
        </div>

        {/* High-Contrast Events Table */}
        <div className="border-4 border-black bg-white overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead className="bg-black text-white text-[11px] uppercase font-mono font-bold tracking-wider">
              <tr>
                <th className="py-4 px-4 border-r border-white/20">Event ID</th>
                <th className="py-4 px-4 border-r border-white/20">Provider</th>
                <th className="py-4 px-4 border-r border-white/20">Type</th>
                <th className="py-4 px-4 border-r border-white/20">Status</th>
                <th className="py-4 px-4 border-r border-white/20">Retries</th>
                <th className="py-4 px-4 border-r border-white/20">Latency</th>
                <th className="py-4 px-4 border-r border-white/20">Received</th>
                <th className="py-4 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y-2 divide-black font-mono">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-black/50 uppercase font-bold italic">
                    No matching events. Trigger a load burst below to see live processing.
                  </td>
                </tr>
              ) : (
                events.map((evt) => (
                  <tr
                    key={evt.id}
                    onClick={() => handleInspect(evt.event_id)}
                    className="hover:bg-[#F2F2F2] transition-colors duration-100 cursor-pointer group"
                  >
                    <td className="py-3 px-4 font-bold text-black border-r-2 border-black">
                      {evt.event_id}
                    </td>
                    <td className="py-3 px-4 font-bold uppercase text-black border-r-2 border-black">
                      {evt.provider}
                    </td>
                    <td className="py-3 px-4 text-black/80 border-r-2 border-black text-xs">
                      {evt.event_type}
                    </td>
                    <td className="py-3 px-4 border-r-2 border-black">
                      <span className={`inline-block text-[10px] px-2 py-0.5 ${getStatusBadgeClass(evt.status)}`}>
                        {evt.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-black border-r-2 border-black font-bold">
                      {evt.retry_count > 0 ? (
                        <span className="text-[#FF3000]">{evt.retry_count} / {evt.max_retries}</span>
                      ) : (
                        '0'
                      )}
                    </td>
                    <td className="py-3 px-4 text-black border-r-2 border-black">
                      {evt.processing_duration_ms ? `${evt.processing_duration_ms} ms` : '-'}
                    </td>
                    <td className="py-3 px-4 text-black/60 text-xs border-r-2 border-black">
                      {formatTimestamp(evt.received_at)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="group-hover:text-[#FF3000] inline-block font-black">
                        →
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Inspection Drawer (Swiss Rectangular Overlay) */}
        {selectedEvent && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-none flex justify-end">
            <div className="bg-white w-full max-w-2xl h-full border-l-4 border-black p-8 overflow-y-auto flex flex-col justify-between font-mono animate-slide-in-right">
              <div>
                <div className="flex items-center justify-between pb-4 border-b-4 border-black mb-6">
                  <div>
                    <span className="text-xs font-black uppercase text-[#FF3000]">Event Audit Log</span>
                    <h3 className="text-2xl font-black uppercase text-black mt-1">{selectedEvent.event_id}</h3>
                  </div>
                  <button
                    onClick={() => setSelectedEvent(null)}
                    className="p-2 border-2 border-black hover:bg-black hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 border-2 border-black p-4 mb-6 bg-[#F2F2F2] text-xs">
                  <div>
                    <span className="text-black/50 uppercase font-black">Provider</span>
                    <div className="font-bold text-black uppercase mt-0.5">{selectedEvent.provider}</div>
                  </div>
                  <div>
                    <span className="text-black/50 uppercase font-black">Event Type</span>
                    <div className="font-bold text-black mt-0.5">{selectedEvent.event_type}</div>
                  </div>
                  <div>
                    <span className="text-black/50 uppercase font-black">Status</span>
                    <div className="mt-0.5">
                      <span className={`inline-block text-[10px] px-2 py-0.5 ${getStatusBadgeClass(selectedEvent.status)}`}>
                        {selectedEvent.status}
                      </span>
                    </div>
                  </div>
                  <div>
                    <span className="text-black/50 uppercase font-black">Retry Count</span>
                    <div className="font-bold text-black mt-0.5">{selectedEvent.retry_count} / {selectedEvent.max_retries}</div>
                  </div>
                </div>

                {/* Attempts Timeline */}
                <div className="mb-6">
                  <div className="text-xs font-black uppercase tracking-wider text-black mb-3 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-[#FF3000]" />
                    <span>Chronological Attempt Execution History ({selectedEvent.attempts?.length || 0})</span>
                  </div>

                  {selectedEvent.attempts && selectedEvent.attempts.length > 0 ? (
                    <div className="space-y-3">
                      {selectedEvent.attempts.map((att) => (
                        <div
                          key={att.id}
                          className={`p-4 border-2 border-black text-xs ${
                            att.status === 'SUCCESS' ? 'bg-[#F2F2F2]' : 'bg-[#FF3000] text-white'
                          }`}
                        >
                          <div className="flex items-center justify-between font-bold mb-1">
                            <span>ATTEMPT #{att.attempt_number} • WORKER: {att.worker_id}</span>
                            <span>{att.duration_ms} ms</span>
                          </div>
                          {att.error_message && (
                            <div className="mt-2 p-2 bg-black text-white text-[11px] font-bold">
                              {att.error_message}
                            </div>
                          )}
                          <div className="text-[10px] opacity-75 mt-1">
                            Timestamp: {formatTimestamp(att.started_at)}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs border-2 border-black p-4 bg-[#F2F2F2] italic text-black/60">
                      No worker attempts executed yet.
                    </div>
                  )}
                </div>

                {/* Raw Payload JSON */}
                <div>
                  <div className="text-xs font-black uppercase tracking-wider text-black mb-2">Raw Ingested Payload</div>
                  <pre className="border-2 border-black bg-black text-white p-4 text-[11px] overflow-x-auto max-h-56">
                    {JSON.stringify(selectedEvent.payload, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="pt-6 border-t-4 border-black flex justify-end">
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="px-6 py-3 bg-black hover:bg-[#FF3000] text-white text-xs font-bold uppercase tracking-wider transition-colors"
                >
                  Close Inspector
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
