export interface EventAttemptItem {
  id: number;
  event_id: string;
  provider: string;
  attempt_number: number;
  worker_id: string;
  status: 'SUCCESS' | 'FAILED';
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  error_message?: string;
  response_status_code?: number;
  is_retryable: boolean;
}

export type EventPriority = 'CRITICAL' | 'HIGH' | 'NORMAL' | 'LOW';
export type SystemMode = 'NORMAL' | 'PRESSURE' | 'DEGRADED' | 'RECOVERY';
export type CircuitBreakerState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

export interface EventItem {
  id: number;
  event_id: string;
  provider: 'stripe' | 'razorpay' | 'github' | 'generic';
  event_type: string;
  priority?: EventPriority;
  payload: Record<string, any>;
  headers?: Record<string, any>;
  status: 'RECEIVED' | 'QUEUED' | 'PROCESSING' | 'SUCCESS' | 'RETRYING' | 'FAILED' | 'DLQ' | 'DUPLICATE' | 'DELAYED' | 'BATCHED' | 'THROTTLED';
  retry_count: number;
  max_retries: number;
  received_at: string;
  queued_at?: string;
  started_at?: string;
  completed_at?: string;
  processing_duration_ms?: number;
  error_message?: string;
  last_error_type?: string;
  is_duplicate: boolean;
  duplicate_count: number;
}

export interface EventDetailItem extends EventItem {
  attempts: EventAttemptItem[];
}

export interface WorkerItem {
  id: string;
  status: 'STARTING' | 'HEALTHY' | 'BUSY' | 'DRAINING' | 'FAILED' | 'STOPPED';
  current_event_id?: string;
  current_event_provider?: string;
  current_event_type?: string;
  processed_count: number;
  success_count: number;
  failure_count: number;
  total_processing_time_ms: number;
  average_duration_ms: number;
  last_heartbeat: string;
  started_at: string;
}

export interface DLQItem {
  id: number;
  dlq_id: string;
  event_id: string;
  provider: string;
  event_type: string;
  payload: Record<string, any>;
  headers?: Record<string, any>;
  failure_reason: string;
  error_trace?: string;
  retry_count: number;
  created_at: string;
  resolved_at?: string;
  is_resolved: boolean;
}

export interface SystemMetrics {
  total_events: number;
  events_per_second: number;
  success_count: number;
  failed_count: number;
  retrying_count: number;
  dlq_count: number;
  duplicate_count: number;
  success_rate: number;
  queue_depth: number;
  pending_events: number;
  active_workers: number;
  total_workers: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  timestamp: string;
  // Adaptive Policy Metrics
  system_mode?: SystemMode;
  circuit_breaker_state?: CircuitBreakerState;
  circuit_breaker_failure_rate?: number;
  circuit_breaker_tripped_count?: number;
  current_concurrency?: number;
  target_concurrency?: number;
  backpressure_delay_ms?: number;
  retry_backoff_multiplier?: number;
  batch_buffer_size?: number;
  critical_events_count?: number;
  high_events_count?: number;
  normal_events_count?: number;
  low_events_count?: number;
  throttled_events_count?: number;
  batched_events_count?: number;
  last_policy_decision?: PolicyDecisionItem;
}

export interface PolicyDecisionItem {
  id?: number;
  decision_id: string;
  timestamp: string;
  previous_mode: SystemMode;
  target_mode: SystemMode;
  trigger_reason: string;
  queue_depth: number;
  p95_latency_ms: number;
  error_rate: number;
  rate_limit_ratio: number;
  concurrency_target: number;
  retry_multiplier: number;
  backpressure_applied: boolean;
  batching_enabled: boolean;
}

export interface CircuitBreakerStatus {
  service_name: string;
  state: CircuitBreakerState;
  failure_count: number;
  success_count: number;
  total_requests: number;
  failure_rate: number;
  consecutive_failures: number;
  cooldown_remaining_s: number;
  is_healthy: boolean;
}

export interface BenchmarkMetrics {
  total_events: number;
  completed_events: number;
  successful_events: number;
  failed_events: number;
  dlq_events: number;
  duplicate_events: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  throughput_eps: number;
  total_duration_s: number;
  concurrency_range: [number, number];
  circuit_breaker_tripped_count: number;
  retry_exhaustions: number;
  critical_event_success_rate: number;
}

export interface BenchmarkResult {
  timestamp: string;
  events_tested: number;
  static_baseline: BenchmarkMetrics;
  adaptive_eventforge: BenchmarkMetrics;
  comparison: {
    throughput_improvement_pct: number;
    p95_latency_reduction_pct: number;
    failure_reduction_pct: number;
    critical_delivery_pct: number;
    recovery_time_seconds: number;
  };
}
