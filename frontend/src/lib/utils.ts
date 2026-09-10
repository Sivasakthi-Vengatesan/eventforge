import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(isoStr?: string): string {
  if (!isoStr) return '-';
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + String(d.getMilliseconds()).padStart(3, '0');
  } catch {
    return isoStr;
  }
}

export function getStatusBadgeClass(status: string): string {
  switch (status?.toUpperCase()) {
    case 'SUCCESS':
    case 'HEALTHY':
      return 'bg-black text-white border-2 border-black font-mono font-bold';
    case 'PROCESSING':
    case 'BUSY':
      return 'bg-[#FF3000] text-white border-2 border-[#FF3000] font-mono font-bold animate-pulse';
    case 'QUEUED':
    case 'RECEIVED':
      return 'bg-[#F2F2F2] text-black border-2 border-black font-mono font-medium';
    case 'RETRYING':
      return 'bg-white text-[#FF3000] border-2 border-[#FF3000] font-mono font-bold';
    case 'DUPLICATE':
      return 'bg-[#F2F2F2] text-black border-2 border-black font-mono font-medium';
    case 'DLQ':
    case 'FAILED':
      return 'bg-[#FF3000] text-white border-2 border-black font-mono font-bold';
    case 'DRAINING':
    case 'STOPPED':
      return 'bg-[#F2F2F2] text-neutral-500 border-2 border-neutral-300 font-mono';
    default:
      return 'bg-white text-black border-2 border-black font-mono';
  }
}
