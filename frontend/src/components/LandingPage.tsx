import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { FadeUp } from './FadeUp';

interface LandingPageProps {
  onExplore: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onExplore }) => {
  const words = ['EVENTS', 'IN.', 'FAILURES', 'OUT.'];

  return (
    <div className="relative w-full h-screen overflow-hidden select-none bg-[#050505]">
      {/* Background video (fixed, behind everything) */}
      <video
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260514_135830_bb6491d1-9b66-4aec-9722-13b4dfe3fb46.mp4"
        autoPlay
        muted
        loop
        playsInline
        className="fixed top-0 left-0 w-full h-screen object-cover z-0 pointer-events-none"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100vh',
          objectFit: 'cover',
          zIndex: 0,
        }}
      />

      {/* Subtle vignette / dark overlay to ensure readability */}
      <div className="fixed inset-0 bg-black/30 z-0 pointer-events-none" />

      {/* Section layout (Full viewport, 100vh, transparent) */}
      <section
        className="relative z-1 flex flex-col justify-center h-screen px-[18px] pt-[90px] pb-[32px] md:px-[32px] md:pt-[70px] md:pb-[32px] max-w-7xl mx-auto"
        style={{
          position: 'relative',
          zIndex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          height: '100vh',
        }}
      >
        {/* Content block */}
        <div
          className="flex flex-col items-start max-w-[720px]"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-start',
            maxWidth: '720px',
          }}
        >
          {/* Heading (<h2>) */}
          <h2
            className="flex flex-wrap m-0 uppercase font-bold text-white tracking-[-0.01em] leading-[1.08]"
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.25em',
              fontSize: 'clamp(26px, 3vw, 42px)',
              fontWeight: 700,
              lineHeight: 1.08,
              letterSpacing: '-0.01em',
              textTransform: 'uppercase',
              color: '#fff',
              margin: 0,
            }}
          >
            {words.map((word, index) => (
              <motion.span
                key={word}
                initial={{ opacity: 0, y: 32 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{
                  duration: 0.7,
                  delay: 0.15 + index * 0.08,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className="inline-block"
              >
                {word}
              </motion.span>
            ))}
          </h2>

          {/* Subtext (<p>) */}
          <FadeUp
            as="p"
            delay={0.9}
            y={24}
            className="text-white/85"
            style={{
              marginTop: '24px',
              fontSize: '14px',
              lineHeight: 1.65,
              color: 'rgba(255, 255, 255, 0.85)',
              maxWidth: '260px',
            }}
          >
            An adaptive event-processing platform built for reliability under pressure.
          </FadeUp>

          {/* Explore Button (<button>) */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{
              duration: 0.7,
              delay: 1.05,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="mt-8"
          >
            <button
              onClick={onExplore}
              className="group relative inline-flex items-center gap-3 px-6 py-3.5 bg-[#FF6A1A] hover:bg-[#C94E0A] active:bg-[#A83F06] text-white font-semibold text-sm uppercase tracking-wider rounded-none border border-[#FF6A1A] hover:border-[#C94E0A] transition-all duration-200 shadow-lg hover:shadow-xl cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#FF6A1A] focus:ring-offset-2 focus:ring-offset-[#050505]"
              style={{
                backgroundColor: '#FF6A1A',
                color: '#FFFFFF',
              }}
            >
              <span>Explore EventForge</span>
              <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1 text-white" />
            </button>
          </motion.div>
        </div>
      </section>
    </div>
  );
};
