import React, { useState } from 'react';

interface NavbarProps {
  onNavigate?: (sectionId: string) => void;
  onGoHome?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onNavigate, onGoHome }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { label: 'Architecture', id: 'architecture' },
    { label: 'Adaptive Policy', id: 'adaptive-policy' },
    { label: 'Priorities', id: 'priority-queue' },
    { label: 'Telemetry', id: 'telemetry' },
    { label: 'Workers', id: 'workers' },
    { label: 'Circuit Breaker', id: 'circuit-breaker' },
    { label: 'Events', id: 'events' },
    { label: 'Benchmark', id: 'benchmark' },
    { label: 'DLQ', id: 'dlq' },
    { label: 'Simulation', id: 'simulation' },
  ];

  const handleLinkClick = (id: string) => {
    setIsMobileMenuOpen(false);
    if (onNavigate) {
      onNavigate(id);
    } else {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleLogoClick = () => {
    if (onGoHome) {
      onGoHome();
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <header className="relative z-20 w-full px-6 py-6 md:px-12 lg:px-20 max-w-7xl mx-auto flex items-center justify-between border-b-2 border-black/10">
      {/* Logo (Left side) */}
      <div 
        onClick={handleLogoClick}
        className="flex items-center gap-3 cursor-pointer group"
        title="Return to Landing Page"
      >
        <span className="text-[21px] sm:text-[24px] tracking-tight text-black font-black select-none uppercase">
          EventForge
        </span>
        <span className="text-[22px] sm:text-[26px] text-swiss-accent select-none font-black leading-none group-hover:rotate-45 transition-transform duration-300">
          ◆
        </span>
        <span className="hidden sm:inline-block font-mono text-[10px] font-bold uppercase tracking-widest bg-black text-white px-2 py-0.5">
          ADAPTIVE v2.4
        </span>
      </div>

      {/* Desktop Nav Links (Center) */}
      <nav className="hidden xl:flex items-center gap-1.5 text-xs text-black font-mono font-bold uppercase tracking-wider select-none">
        {navItems.map((item, index) => (
          <React.Fragment key={item.id}>
            <button
              onClick={() => handleLinkClick(item.id)}
              className="hover:text-swiss-accent transition-colors px-1 cursor-pointer focus:outline-none"
            >
              {item.label}
            </button>
            {index < navItems.length - 1 && (
              <span className="text-black/30 select-none">/</span>
            )}
          </React.Fragment>
        ))}
      </nav>

      {/* Desktop CTA (Right) */}
      <div className="hidden sm:flex items-center gap-4">
        {onGoHome && (
          <button
            onClick={onGoHome}
            className="text-xs font-mono font-bold uppercase hover:text-swiss-accent underline underline-offset-4 cursor-pointer"
          >
            ← COVER
          </button>
        )}
        <button
          onClick={() => handleLinkClick('simulation')}
          className="bg-black hover:bg-swiss-accent text-white font-mono text-xs font-black uppercase px-4 py-2 border-2 border-black transition-all cursor-pointer"
        >
          LIVE TRAFFIC
        </button>
      </div>

      {/* Mobile Hamburger Button */}
      <button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        className="xl:hidden z-30 flex flex-col justify-center items-center w-8 h-8 gap-[5px] focus:outline-none"
        aria-label="Toggle navigation menu"
      >
        <span
          className={`w-6 h-[2px] bg-black transition-all duration-300 transform ${
            isMobileMenuOpen ? 'rotate-45 translate-y-[7px]' : ''
          }`}
        />
        <span
          className={`w-6 h-[2px] bg-black transition-all duration-300 ${
            isMobileMenuOpen ? 'opacity-0' : 'opacity-100'
          }`}
        />
        <span
          className={`w-6 h-[2px] bg-black transition-all duration-300 transform ${
            isMobileMenuOpen ? '-rotate-45 -translate-y-[7px]' : ''
          }`}
        />
      </button>

      {/* Mobile Navigation Overlay */}
      <div
        className={`fixed inset-0 z-[9] bg-white/95 backdrop-blur-sm flex flex-col items-center justify-center gap-6 transition-opacity duration-300 xl:hidden ${
          isMobileMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
      >
        <div className="flex flex-col items-center gap-4 text-base font-mono font-bold uppercase text-black">
          {onGoHome && (
            <button
              onClick={() => {
                setIsMobileMenuOpen(false);
                onGoHome();
              }}
              className="text-swiss-accent font-bold"
            >
              ← RETURN TO COVER
            </button>
          )}
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleLinkClick(item.id)}
              className="hover:text-swiss-accent transition-colors focus:outline-none"
            >
              {item.label}
            </button>
          ))}
          <button
            onClick={() => handleLinkClick('simulation')}
            className="mt-4 bg-black text-white px-6 py-2 border-2 border-black"
          >
            RUN TRAFFIC SIMULATION
          </button>
        </div>
      </div>
    </header>
  );
};
