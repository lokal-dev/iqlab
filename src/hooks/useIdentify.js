import { useState, useCallback, useRef } from 'react';

/**
 * Calls the real FastAPI /api/identify endpoint.
 * POST multipart/form-data { audio: Blob } → JSON { results: [] }
 */
async function callIdentifyAPI(audioBlob, signal) {
  const fd = new FormData();
  fd.append('audio', audioBlob, 'recording.webm');

  const res = await fetch('/api/identify', {
    method: 'POST',
    body: fd,
    signal,
  });

  if (res.status === 400) {
    const data = await res.json();
    throw new Error(data.detail || 'INVALID_FILE');
  }

  if (!res.ok) {
    throw new Error('SERVER_ERROR');
  }

  return res.json();
}

/**
 * Hook for audio identification flow.
 * States: idle | processing | results | zero_match | error
 */
export function useIdentify() {
  const [state, setState] = useState('idle');
  const [results, setResults] = useState([]);
  const [errorType, setErrorType] = useState(null);
  const abortCtrlRef = useRef(null);

  const identify = useCallback(async (audioBlob) => {
    // Cancel any in-flight request
    if (abortCtrlRef.current) {
      abortCtrlRef.current.abort();
    }
    const ctrl = new AbortController();
    abortCtrlRef.current = ctrl;

    setState('processing');
    setResults([]);
    setErrorType(null);

    try {
      const data = await callIdentifyAPI(audioBlob, ctrl.signal);

      if (!data.results || data.results.length === 0) {
        setState('zero_match');
      } else {
        setResults(data.results);
        setState('results');
      }
    } catch (err) {
      if (err.name === 'AbortError') return; // User cancelled

      if (err.message === 'INVALID_FILE') {
        setErrorType('INVALID_FILE');
      } else {
        setErrorType('NETWORK_ERROR');
      }
      setState('error');
    }
  }, []);

  function cancel() {
    if (abortCtrlRef.current) {
      abortCtrlRef.current.abort();
      abortCtrlRef.current = null;
    }
    setState('idle');
    setResults([]);
    setErrorType(null);
  }

  function reset() {
    setState('idle');
    setResults([]);
    setErrorType(null);
  }

  return { state, results, errorType, identify, cancel, reset };
}
