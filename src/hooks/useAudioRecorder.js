import { useState, useRef, useEffect } from 'react';

/**
 * Custom hook for mic recording via MediaRecorder API.
 * Returns: { isRecording, seconds, audioBlob, startRecording, stopRecording, reset }
 */
export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  // Auto-stop at 30s to keep it reasonable (backend trims to 10s anyway)
  const MAX_SECONDS = 30;

  useEffect(() => {
    return () => {
      clearInterval(timerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mr = new MediaRecorder(stream, { mimeType: getSupportedMimeType() });
      mediaRecorderRef.current = mr;
      chunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mr.mimeType });
        setAudioBlob(blob);
        stream.getTracks().forEach(t => t.stop());
      };

      mr.start(200);
      setIsRecording(true);
      setSeconds(0);
      setAudioBlob(null);

      timerRef.current = setInterval(() => {
        setSeconds(s => {
          if (s + 1 >= MAX_SECONDS) {
            stopRecordingInternal(mr);
            return s + 1;
          }
          return s + 1;
        });
      }, 1000);

    } catch {
      throw new Error('MIC_DENIED');
    }
  }

  function stopRecordingInternal(mr) {
    clearInterval(timerRef.current);
    if (mr && mr.state !== 'inactive') mr.stop();
    setIsRecording(false);
  }

  function stopRecording() {
    stopRecordingInternal(mediaRecorderRef.current);
  }

  function reset() {
    setIsRecording(false);
    setSeconds(0);
    setAudioBlob(null);
    chunksRef.current = [];
  }

  return { isRecording, seconds, audioBlob, startRecording, stopRecording, reset };
}

function getSupportedMimeType() {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
  ];
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return '';
}
