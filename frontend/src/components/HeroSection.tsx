import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ArrowRight } from 'lucide-react';
import { useTypewriter } from '../hooks/useTypewriter';
import { useVideoScrubbing } from '../hooks/useVideoScrubbing';

interface HeroSectionProps {
  selectedServices: string[];
  onToggleService: (service: string) => void;
  onExploreClick: () => void;
}

const SERVICE_OPTIONS = [
  "Webhook Gateway",
  "Redis Streams",
  "Worker Pool",
  "PostgreSQL",
  "Retry Engine",
  "Dead Letter Queue",
  "Monitoring"
];

export const HeroSection: React.FC<HeroSectionProps> = ({
  selectedServices,
  onToggleService,
  onExploreClick,
}) => {
  const videoRef = useVideoScrubbing();
  const { displayed, done } = useTypewriter("events in.\nsystems out.", 38, 600);

  return (
    <div className="relative w-full overflow-hidden">
      {/* Background Video Component (with Native Scrubbing) */}
      <div className="order-last lg:order-none relative lg:absolute lg:inset-0 lg:z-0 overflow-hidden pointer-events-none w-full aspect-square md:aspect-video lg:aspect-auto lg:h-full bg-neutral-50 lg:bg-transparent">
        <video
          ref={videoRef}
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260601_110537_3a579fa0-7bbc-4d94-9d25-0e816c7840f5.mp4"
          muted
          playsInline
          preload="auto"
          className="w-full h-full object-cover object-right lg:object-right-bottom opacity-90 transition-opacity duration-700"
        />
      </div>

      {/* Content Layout Container */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 pt-12 pb-24 md:px-12 lg:px-20 lg:pt-16 lg:pb-36 flex flex-col justify-start">
        {/* Typewriter Hook and Headline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl"
        >
          <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-medium tracking-tight text-neutral-900 leading-[1.05] whitespace-pre-line select-none">
            {displayed}
            {!done && (
              <span className="inline-block w-2.5 h-9 sm:h-12 md:h-14 lg:h-16 bg-neutral-900 ml-1.5 align-middle animate-blink" />
            )}
          </h1>
        </motion.div>

        {/* Secondary Description Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mt-8"
        >
          <p className="text-lg md:text-xl text-[#5A635A] leading-relaxed font-normal mb-14 max-w-2xl">
            A high-throughput async gateway for webhooks. Accept events fast, process them safely, retry failures automatically, and route unrecoverable events to a dead-letter queue.
          </p>
        </motion.div>

        {/* Interactive Multi-Select Service Pills Section */}
        <div className="max-w-3xl">
          <h2 className="text-2xl font-medium tracking-tight text-neutral-900 mb-2">
            What do you want to explore?
          </h2>
          <p className="text-sm md:text-base opacity-85 text-[#738273] mb-8">
            Select the system components
          </p>

          <div className="flex flex-wrap gap-2.5 sm:gap-3">
            {SERVICE_OPTIONS.map((service) => {
              const isSelected = selectedServices.includes(service);
              return (
                <motion.button
                  key={service}
                  onClick={() => onToggleService(service)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-full text-sm sm:text-base font-medium transition-all duration-200 cursor-pointer ${
                    isSelected
                      ? 'bg-[#1C2E1E] text-white shadow-md shadow-emerald-950/5 transform'
                      : 'bg-white text-[#1C2E1E] border border-[#F1F3F1] hover:bg-[#F1F3F1]/55'
                  }`}
                >
                  <AnimatePresence>
                    {isSelected && (
                      <motion.span
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ type: "spring", stiffness: 300, damping: 20 }}
                      >
                        <Check className="w-4 h-4 text-emerald-400 stroke-[2.5]" />
                      </motion.span>
                    )}
                  </AnimatePresence>
                  <span>{service}</span>
                </motion.button>
              );
            })}
          </div>

          {/* Contingent Feedback Status Banner */}
          <div className="mt-8 min-h-[60px]">
            {selectedServices.length === 0 ? (
              <p className="opacity-50 italic text-xs text-[#5A635A] py-3">
                Select components to explore the architecture.
              </p>
            ) : (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                className="bg-[#FAFBF9] border border-neutral-200/80 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm"
              >
                <div className="text-xs sm:text-sm text-neutral-800 font-medium leading-relaxed">
                  <span className="text-neutral-500">Exploring: </span>
                  <span className="text-[#1C2E1E] font-semibold">{selectedServices.join(", ")}</span>
                </div>
                <button
                  onClick={onExploreClick}
                  className="inline-flex items-center gap-1.5 text-[#4D6D47] uppercase text-xs font-bold tracking-wider hover:opacity-80 transition-opacity whitespace-nowrap group focus:outline-none"
                >
                  <span>Explore</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </button>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
