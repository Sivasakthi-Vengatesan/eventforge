import { useEffect, useRef } from 'react';

export function useVideoScrubbing() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const prevXRef = useRef<number | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Mobile Autoplay Hook: width < 1024
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        video.autoplay = true;
        video.play().catch(() => {
          // Autoplay policy fallback
        });
      }
    };

    handleResize();

    // Desktop Mouse Scrubbing Hook
    let isSeeking = false;
    let targetTime = 0;

    const handleSeeked = () => {
      isSeeking = false;
    };

    video.addEventListener('seeked', handleSeeked);

    const handleMouseMove = (e: MouseEvent) => {
      if (window.innerWidth < 1024) {
        return; // Ignore scrubbing on mobile frames
      }

      if (prevXRef.current === null) {
        prevXRef.current = e.clientX;
        return;
      }

      const delta = e.clientX - prevXRef.current;
      prevXRef.current = e.clientX;

      if (!video.duration || isNaN(video.duration)) return;

      const duration = video.duration;
      // Calculate target scrub time based on (delta / window.innerWidth) * 0.8 * video.duration
      const timeDelta = (delta / window.innerWidth) * 0.8 * duration;
      targetTime = Math.max(0, Math.min(duration, (video.currentTime || 0) + timeDelta));

      if (!isSeeking) {
        isSeeking = true;
        video.currentTime = targetTime;
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      video.removeEventListener('seeked', handleSeeked);
    };
  }, []);

  return videoRef;
}
