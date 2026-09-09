import React from 'react';
import { SystemMetrics, EventPriority } from '../types';

interface PriorityQueueViewProps {
  metrics: SystemMetrics | null;
}

export const PriorityQueueView: React.FC<PriorityQueueViewProps> = ({ metrics }) => {
  const criticalCount = metrics?.critical_events_count || 0;
  const highCount = metrics?.high_events_count || 0;
  const normalCount = metrics?.normal_events_count || 0;
  const lowCount = metrics?.low_events_count || 0;
  const throttledCount = metrics?.throttled_events_count || 0;
  const batchedCount = metrics?.batched_events_count || 0;

  const totalPriorityEvents = criticalCount + highCount + normalCount + lowCount || 1;

  const priorityTiers: {
    priority: EventPriority;
    tier: string;
    count: number;
    color: string;
    bg: string;
    border: string;
    description: string;
    examples: string[];
    sla: string;
    backpressure: string;
    batching: string;
  }[] = [
    {
      priority: 'CRITICAL',
      tier: 'TIER 01',
      count: criticalCount,
      color: 'text-white',
      bg: 'bg-black',
      border: 'border-black',
      description: 'High-stakes financial and transactional webhooks. Strict zero-loss guarantee with zero backpressure delays.',
      examples: ['payment_intent.succeeded', 'charge.refunded', 'payment.authorized', 'charge.dispute.created'],
      sla: '< 100ms processing',
      backpressure: 'IMMUNE (0ms DELAY)',
      batching: 'DISALLOWED (ACID ISOLATED)'
    },
    {
      priority: 'HIGH',
      tier: 'TIER 02',
      count: highCount,
      color: 'text-black',
      bg: 'bg-neutral-100',
      border: 'border-black',
      description: 'Core business state updates and deployment triggers requiring rapid asynchronous execution.',
      examples: ['invoice.paid', 'customer.subscription.created', 'github.push', 'payment.captured'],
      sla: '< 250ms processing',
      backpressure: 'MINIMAL (≤ 10ms)',
      batching: 'DISALLOWED'
    },
    {
      priority: 'NORMAL',
      tier: 'TIER 03',
      count: normalCount,
      color: 'text-black',
      bg: 'bg-white',
      border: 'border-black',
      description: 'Standard lifecycle events and user mutations processed with standard exponential retry policies.',
      examples: ['customer.updated', 'customer.source.created', 'github.pull_request', 'razorpay.order.paid'],
      sla: '< 1000ms processing',
      backpressure: 'STANDARD DELAY',
      batching: 'OPTIONAL (RECOVERY ONLY)'
    },
    {
      priority: 'LOW',
      tier: 'TIER 04',
      count: lowCount,
      color: 'text-black',
      bg: 'bg-neutral-50',
      border: 'border-neutral-400',
      description: 'Non-critical telemetry, audit records, and auxiliary events that can be dynamically throttled or batched during load.',
      examples: ['analytics.tracked', 'audit.log', 'github.watch', 'github.star', 'generic.ping'],
      sla: 'BEST EFFORT',
      backpressure: 'THROTTLED DURING PRESSURE',
      batching: 'ENABLED (CHUNKS OF 10)'
    }
  ];

  return (
    <section id="priority-queue" className="py-20 px-6 md:px-12 lg:px-20 max-w-7xl mx-auto border-b-4 border-black">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 pb-6 border-b-2 border-black gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-xs font-black uppercase tracking-widest text-swiss-accent">
              SECTION 03 // TRAFFIC DIFFERENTIATION
            </span>
            <span className="h-1.5 w-1.5 bg-black" />
            <span className="font-mono text-xs uppercase font-bold text-neutral-500">
              ADAPTIVE ROUTING MATRIX
            </span>
          </div>
          <h2 className="text-4xl md:text-5xl font-black uppercase tracking-tight text-black">
            Priority Queue Distribution
          </h2>
          <p className="text-sm md:text-base font-bold text-neutral-600 uppercase tracking-wide mt-2 max-w-3xl">
            Multi-tiered event routing ensures mission-critical financial webhooks maintain strict SLA execution while non-critical telemetry events absorb backpressure delays and dynamic batching.
          </p>
        </div>

        {/* Aggregate Counters */}
        <div className="flex items-center gap-4">
          <div className="border-2 border-black p-3 bg-white text-right">
            <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block">THROTTLED (LOW)</span>
            <span className="text-xl font-mono font-black text-swiss-accent">{throttledCount}</span>
          </div>
          <div className="border-2 border-black p-3 bg-white text-right">
            <span className="text-[10px] font-mono font-bold uppercase text-neutral-500 block">BATCHED BUFFER</span>
            <span className="text-xl font-mono font-black text-black">{batchedCount}</span>
          </div>
        </div>
      </div>

      {/* 4-Tier Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {priorityTiers.map((tier) => {
          const pct = Math.round((tier.count / totalPriorityEvents) * 100);
          return (
            <div
              key={tier.priority}
              className={`border-2 ${tier.border} ${tier.bg} p-6 flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-center justify-between pb-3 mb-4 border-b border-black/20">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-500">
                    {tier.tier}
                  </span>
                  <span className={`text-xs font-mono font-black px-2 py-0.5 ${tier.priority === 'CRITICAL' ? 'bg-swiss-accent text-white' : 'bg-black text-white'}`}>
                    {tier.priority}
                  </span>
                </div>

                <div className="mb-4">
                  <div className={`text-3xl font-mono font-black ${tier.color}`}>
                    {tier.count}
                  </div>
                  <div className="text-[10px] font-mono font-bold uppercase text-neutral-400 mt-1">
                    {pct}% OF INGESTED VOLUME
                  </div>
                </div>

                <p className={`text-xs font-medium uppercase mb-6 leading-relaxed ${tier.priority === 'CRITICAL' ? 'text-neutral-300' : 'text-neutral-700'}`}>
                  {tier.description}
                </p>
              </div>

              <div className="pt-4 border-t border-black/20 space-y-2 text-[11px] font-mono">
                <div className="flex justify-between">
                  <span className="text-neutral-500">SLA TARGET:</span>
                  <span className={`font-bold ${tier.color}`}>{tier.sla}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500">BACKPRESSURE:</span>
                  <span className={`font-bold ${tier.priority === 'CRITICAL' ? 'text-emerald-400' : tier.color}`}>{tier.backpressure}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500">BATCH SAFETY:</span>
                  <span className={`font-bold ${tier.color}`}>{tier.batching}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Priority Rules & Safety Invariants Table */}
      <div className="border-2 border-black p-6 bg-neutral-50">
        <div className="flex items-center gap-3 pb-3 mb-4 border-b border-black/20">
          <span className="text-swiss-accent font-black">◆</span>
          <span className="text-xs font-mono font-black uppercase tracking-wider text-black">
            ADAPTIVE EVENT DISPATCH SAFETY INVARIANTS
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs font-mono">
          <div>
            <span className="font-black text-black block mb-1">1. ZERO-LATENCY FINANCIAL BYPASS</span>
            <p className="text-neutral-600 uppercase">
              Financial and refund events (<span className="text-black font-bold">CRITICAL</span>) bypass adaptive backpressure queues and jump directly to dedicated priority worker channels.
            </p>
          </div>
          <div>
            <span className="font-black text-black block mb-1">2. DYNAMIC LOW-TIER SHEDDING</span>
            <p className="text-neutral-600 uppercase">
              When system enters <span className="text-amber-600 font-bold">PRESSURE</span> or <span className="text-swiss-accent font-bold">DEGRADED</span> mode, non-critical telemetry events are throttled and accumulated into compressed batches.
            </p>
          </div>
          <div>
            <span className="font-black text-black block mb-1">3. FINANCIAL BATCH IMMUNITY</span>
            <p className="text-neutral-600 uppercase">
              Events flagged with strict financial semantics are strictly barred from batching to prevent cross-event rollback corruption in downstream payment systems.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
