import { useState, useEffect, useRef } from "react";

export function usePolling(fetchFn, intervalMs = 10000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // Track the previous fetchFn identity to detect when the query changes
  const fetchFnRef = useRef(fetchFn);

  useEffect(() => {
    fetchFnRef.current = fetchFn;
  }, [fetchFn]);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const result = await fetchFnRef.current();
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
          // Don't wipe existing data on a transient error
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    // Re-fetch immediately whenever fetchFn changes (e.g. date/symbol change)
    setLoading(true);
    poll();

    const id = setInterval(poll, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  // fetchFn in deps ensures effect restarts when date/symbol changes
  }, [fetchFn, intervalMs]);

  return { data, error, loading };
}
