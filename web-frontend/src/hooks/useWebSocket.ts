import { useEffect, useRef, useCallback, useState } from 'react';
import { wsClient } from '../services/api';

interface UseWebSocketReturn {
  isConnected: boolean;
  sendMessage: (data: any) => void;
  lastMessage: any;
  connectionError: string | null;
}

export function useWebSocket(onMessage?: (data: any) => void): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const sendMessage = useCallback((data: any) => {
    wsClient.send(data);
  }, []);

  useEffect(() => {
    let mounted = true;

    const connect = async () => {
      try {
        setConnectionError(null);
        const ws = await wsClient.connect();
        
        if (!mounted) return;
        
        wsRef.current = ws;
        setIsConnected(true);

        wsClient.onMessage((data) => {
          if (!mounted) return;
          
          setLastMessage(data);
          onMessage?.(data);
        });

      } catch (error) {
        if (!mounted) return;
        
        setConnectionError(error instanceof Error ? error.message : 'Connection failed');
        setIsConnected(false);
      }
    };

    connect();

    return () => {
      mounted = false;
      setIsConnected(false);
      wsClient.disconnect();
    };
  }, [onMessage]);

  return {
    isConnected,
    sendMessage,
    lastMessage,
    connectionError,
  };
}