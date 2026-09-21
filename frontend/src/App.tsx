import React, { useState } from 'react';
import { LandingPage } from './components/LandingPage';
import { Navbar } from './components/Navbar';
import { ArchitectureView } from './components/ArchitectureView';
import { AdaptivePolicyView } from './components/AdaptivePolicyView';
import { PriorityQueueView } from './components/PriorityQueueView';
import { DashboardOverview } from './components/DashboardOverview';
import { QueueWorkerMonitor } from './components/QueueWorkerMonitor';
import { CircuitBreakerView } from './components/CircuitBreakerView';
import { EventExplorer } from './components/EventExplorer';
import { BenchmarkView } from './components/BenchmarkView';
import { DLQManager } from './components/DLQManager';
import { LiveGenerator } from './components/LiveGenerator';
import { SystemHealth } from './components/SystemHealth';
import { useRheosWS } from './hooks/useRheosWS';

import { SwissLandingPage } from './components/landing/SwissLandingPage';

export function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'dashboard'>('landing');

  const [selectedServices, setSelectedServices] = useState<string[]>([
    "Webhook Gateway",
    "Redis Streams",
    "Worker Pool",
    "PostgreSQL",
    "Retry Engine",
    "Dead Letter Queue",
    "Monitoring",
    "Adaptive Policy Engine"
  ]);

  const { isConnected, metrics } = useRheosWS();

  const handleToggleService = (service: string) => {
    setSelectedServices((prev) =>
      prev.includes(service)
        ? prev.filter((s) => s !== service)
        : [...prev, service]
    );
  };

  const handleNavigate = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // If in landing view, show the Swiss Poster Choreographed Landing Page
  if (currentView === 'landing') {
    return <SwissLandingPage onExplore={() => setCurrentView('dashboard')} />;
  }

  // Dashboard View: Comprehensive Rheos Platform
  return (
    <div className="relative bg-white text-neutral-900 font-sans selection:bg-[#EAECE9] selection:text-[#1C2E1E] antialiased overflow-x-hidden flex flex-col lg:block lg:min-h-screen">
      {/* Interactive Navbar */}
      <Navbar
        onNavigate={handleNavigate}
        onGoHome={() => setCurrentView('landing')}
      />

      {/* 01. ARCHITECTURE — System Design Specification */}
      <ArchitectureView
        selectedServices={selectedServices}
        onSelectService={handleToggleService}
      />

      {/* 02. ADAPTIVE POLICY ENGINE — Autonomous Feedback Loop & Scaling */}
      <AdaptivePolicyView
        metrics={metrics}
      />

      {/* 03. PRIORITY QUEUE DISTRIBUTION — 4-Tier Routing & Safety Matrix */}
      <PriorityQueueView
        metrics={metrics}
      />

      {/* 04. TELEMETRY — Live Pipeline Observability & Latency */}
      <DashboardOverview
        metrics={metrics}
        isConnected={isConnected}
      />

      {/* 05. CONCURRENCY — Redis Streams & Consumer Group Fleet */}
      <QueueWorkerMonitor
        queueDepth={metrics?.queue_depth || 0}
        pendingCount={metrics?.pending_events || 0}
      />

      {/* 06. CIRCUIT BREAKER — Downstream Reliability & Chaos Injection */}
      <CircuitBreakerView />

      {/* 07. AUDIT TRAIL — Real-Time Event Ledger & Inspect */}
      <EventExplorer />

      {/* 08. EMPIRICAL BENCHMARK — Static Baseline vs. Adaptive Rheos */}
      <BenchmarkView />

      {/* 09. FAULT ISOLATION — Dead Letter Queue Quarantine */}
      <DLQManager />

      {/* 10. SIMULATION — Traffic Burst & Chaos Scenario Suite */}
      <LiveGenerator />

      {/* 11. INFRASTRUCTURE — Subsystem Health Diagnostics */}
      <SystemHealth isWsConnected={isConnected} />

      {/* Swiss International Engineering Footer */}
      <footer className="border-t-4 border-black bg-black text-white py-16 px-6 md:px-12 lg:px-20">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl font-black tracking-tight text-white uppercase">Rheos</span>
              <span className="text-swiss-accent text-xl">◆</span>
              <span className="text-xs font-mono font-bold uppercase tracking-widest text-neutral-400">
                SWISS SPEC v2.4
              </span>
            </div>
            <p className="text-xs font-bold text-neutral-400 mt-2 uppercase tracking-wide max-w-md">
              Adaptive Event Reliability & Processing Platform. Objective Communication, Mathematical Structure, Zero-Loss Ingestion.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 text-xs font-mono uppercase font-bold text-neutral-300">
            <div className="flex flex-col gap-1">
              <span className="text-neutral-500 text-[10px]">STACK ARCHITECTURE</span>
              <span>FASTAPI • REDIS STREAMS • SQLITE/PG • REACT • FRAMER</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-neutral-500 text-[10px]">ADAPTIVE ENGINE</span>
              <span className="text-swiss-accent">FEEDBACK CONTROL • CIRCUIT BREAKER • PRIORITY BYPASS</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
