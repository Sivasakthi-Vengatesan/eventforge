import { useEffect, useState, useRef } from 'react';

export interface StageProgress {
  p0: number; // Hero stage progress [0, 1]
  p1: number; // Wipe stage progress [0, 1]
  p2: number; // Timeline stage progress [0, 1]
  p3: number; // Route map stage progress [0, 1]
  scrollY: number;
}

export function useScrollStages() {
  const [progress, setProgress] = useState<StageProgress>({
    p0: 0,
    p1: 0,
    p2: 0,
    p3: 0,
    scrollY: 0,
  });

  const stage0Ref = useRef<HTMLDivElement | null>(null);
  const stage1Ref = useRef<HTMLDivElement | null>(null);
  const stage2Ref = useRef<HTMLDivElement | null>(null);
  const stage3Ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let rafId: number | null = null;

    const calcProgress = (el: HTMLElement | null): number => {
      if (!el) return 0;
      const rect = el.getBoundingClientRect();
      const top = rect.top;
      const height = rect.height;
      const windowHeight = window.innerHeight;
      const totalScrollable = height - windowHeight;
      if (totalScrollable <= 0) return 0;

      // When el top is at 0, progress = 0. When el bottom is at window bottom, progress = 1.
      const raw = -top / totalScrollable;
      return Math.max(0, Math.min(1, raw));
    };

    const update = () => {
      const p0 = calcProgress(stage0Ref.current);
      const p1 = calcProgress(stage1Ref.current);
      const p2 = calcProgress(stage2Ref.current);
      const p3 = calcProgress(stage3Ref.current);
      const scrollY = window.scrollY || window.pageYOffset;

      setProgress({ p0, p1, p2, p3, scrollY });

      // Also set CSS variables on documentElement for CSS-driven transitions
      document.documentElement.style.setProperty('--p0', p0.toFixed(4));
      document.documentElement.style.setProperty('--p1', p1.toFixed(4));
      document.documentElement.style.setProperty('--p2', p2.toFixed(4));
      document.documentElement.style.setProperty('--p3', p3.toFixed(4));
    };

    const onScroll = () => {
      if (rafId === null) {
        rafId = requestAnimationFrame(() => {
          update();
          rafId = null;
        });
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    update();

    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, []);

  return {
    progress,
    stage0Ref,
    stage1Ref,
    stage2Ref,
    stage3Ref,
  };
}
