import { useEffect, useState, useRef, useCallback } from 'react';
import { SystemMetrics } from '../types';

export function useRheosWS(onEventReceived?: (data: any) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const connect = useCallback(() => {
    try {
      let wsUrl: string;
      
      const customWsUrl = import.meta.env.VITE_WS_URL;
      const customApiUrl = import.meta.env.VITE_API_URL;

      if (customWsUrl) {
        wsUrl = customWsUrl;
      } else if (customApiUrl) {
        const clean = customApiUrl.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://').replace(/\/+$/, '');
        wsUrl = `${clean}/ws/monitor`;
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        if (window.location.port === '5173' || window.location.port === '3000') {
          wsUrl = `${protocol}//${window.location.hostname}:8000/ws/monitor`;
        } else {
          wsUrl = `${protocol}//${window.location.host}/ws/monitor`;
        }
      }

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;


      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'INITIAL_SNAPSHOT' || message.type === 'METRICS_UPDATE') {
            setMetrics(message.data);
          }
          if (onEventReceived) {
            onEventReceived(message);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Attempt reconnect after 2 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch (e) {
      console.error('WebSocket connection initialization failed', e);
      setIsConnected(false);
    }
  }, [onEventReceived]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { isConnected, metrics };
}
