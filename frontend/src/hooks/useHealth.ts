import { useCallback, useEffect, useRef, useState } from 'react';
import { checkHealth, ApiError } from '../api/client';
import type { HealthStatus } from '../types/api';

const POLL_INTERVAL_MS = 30_000;

interface UseHealthResult {
  status: HealthStatus | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useHealth(): UseHealthResult {
  const [status, setStatus]   = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);
  const timerRef              = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkHealth();
      setStatus(data);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : 'Failed to reach backend health endpoint.';
      setError(msg);
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetch();

    timerRef.current = setInterval(() => {
      void fetch();
    }, POLL_INTERVAL_MS);

    return () => {
      if (timerRef.current !== null) {
        clearInterval(timerRef.current);
      }
    };
  }, [fetch]);

  return { status, loading, error, refetch: fetch };
}
