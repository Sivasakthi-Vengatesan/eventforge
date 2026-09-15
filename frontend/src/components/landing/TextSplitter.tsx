import React, { useEffect, useRef } from 'react';

interface SplitTextProps {
  text: string;
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span' | 'div';
  className?: string;
  baseDelayMs?: number;
  staggerMs?: number;
  highlightWords?: string[];
  highlightColor?: string;
}

export const SplitText: React.FC<SplitTextProps> = ({
  text,
  as = 'div',
  className = '',
  baseDelayMs = 0,
  staggerMs = 36,
  highlightWords = [],
  highlightColor = '#DC201E',
}) => {
  const containerRef = useRef<HTMLElement | null>(null);
  const words = text.split(/\s+/).filter(Boolean);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed');
          }
        });
      },
      { threshold: 0.12 }
    );

    observer.observe(el);

    return () => {
      observer.disconnect();
    };
  }, []);

  const Tag = as as any;

  return (
    <Tag ref={containerRef} className={`${className} flex flex-wrap gap-x-[0.25em] gap-y-0`} data-rev style={{ '--d': `${baseDelayMs}ms` } as React.CSSProperties}>
      {words.map((word, i) => {
        const isHighlighted = highlightWords.some(
          (hw) => hw.toLowerCase() === word.toLowerCase() || word.toLowerCase().includes(hw.toLowerCase())
        );
        const delay = baseDelayMs + i * staggerMs;

        return (
          <span
            key={i}
            className="rev-word inline-block"
            style={{
              '--d': `${delay}ms`,
              color: isHighlighted ? highlightColor : undefined,
            } as React.CSSProperties}
          >
            {word}
          </span>
        );
      })}
    </Tag>
  );
};
