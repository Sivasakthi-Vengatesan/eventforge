import { SystemMetrics, EventItem, EventDetailItem, WorkerItem, DLQItem } from '../types';

const rawApiUrl = import.meta.env.VITE_API_URL || '';
const cleanApiUrl = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;
const API_BASE = cleanApiUrl ? `${cleanApiUrl}/api/v1` : '/api/v1';


export async function fetchMetrics(): Promise<SystemMetrics> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function fetchEvents(params: {
  provider?: string;
  status?: string;
  event_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<{ total: number; page: number; page_size: number; items: EventItem[] }> {
  const q = new URLSearchParams();
  if (params.provider) q.set('provider', params.provider);
  if (params.status) q.set('status', params.status);
  if (params.event_type) q.set('event_type', params.event_type);
  if (params.search) q.set('search', params.search);
  if (params.page) q.set('page', String(params.page));
  if (params.page_size) q.set('page_size', String(params.page_size));

  const res = await fetch(`${API_BASE}/events?${q.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function fetchEventDetail(eventId: string): Promise<EventDetailItem> {
  const res = await fetch(`${API_BASE}/events/${eventId}`);
  if (!res.ok) throw new Error('Failed to fetch event detail');
  return res.json();
}

export async function fetchWorkers(): Promise<WorkerItem[]> {
  const res = await fetch(`${API_BASE}/workers`);
  if (!res.ok) throw new Error('Failed to fetch workers');
  return res.json();
}

export async function restartWorker(workerId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/workers/${workerId}/restart`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to restart worker');
}

export async function killWorker(workerId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/workers/${workerId}/kill`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to crash worker');
}

export async function fetchDLQ(): Promise<{ total: number; items: DLQItem[] }> {
  const res = await fetch(`${API_BASE}/dlq`);
  if (!res.ok) throw new Error('Failed to fetch DLQ');
  return res.json();
}

export async function retryDLQ(dlqId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/dlq/${dlqId}/retry`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to retry DLQ event');
}

export async function deleteDLQ(dlqId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/dlq/${dlqId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete DLQ event');
}

export async function ingestSampleWebhook(provider: string, payload: any, headers: Record<string, string> = {}): Promise<any> {
  const res = await fetch(`${API_BASE}/webhooks/${provider}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function getMockConfig(): Promise<any> {
  const res = await fetch(`/mock/config`);
  return res.json();
}

export async function updateMockConfig(cfg: any): Promise<any> {
  const res = await fetch(`/mock/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cfg),
  });
  return res.json();
}
