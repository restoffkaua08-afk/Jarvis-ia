import { useState, useEffect, useRef, useCallback } from 'react';

export type VoiceAgentState = 'Idle' | 'Listening' | 'Thinking' | 'Speaking';

export function useVoiceAgent() {
  const [state, setState] = useState<VoiceAgentState>('Idle');
  const [amplitude, setAmplitude] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const connect = useCallback(() => {
    // ponytail: hardcoded backend URL, move to config if multi-env
    const ws = new WebSocket('ws://localhost:8000/voice');

    ws.onopen = () => {
      console.log('VoiceAgent connected');
      setState('Idle');
    };

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'state_transition') {
        setState(data.state);
      } else if (data.type === 'audio_chunk') {
        // Handle incoming audio playback from AI
        playAudioChunk(data.chunk);
      }
    };

    ws.onclose = () => {
      console.log('VoiceAgent disconnected');
      setState('Idle');
      wsRef.current = null;
    };

    wsRef.current = ws;
  }, []);

  const startListening = async () => {
    try {
      // Handle browser autoplay block
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const source = audioContextRef.current.createMediaStreamSource(stream);
      const analyser = audioContextRef.current.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Start streaming to backend
      wsRef.current?.send(JSON.stringify({ type: 'start_listening' }));
      setState('Listening');

      // RMS amplitude tracking
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const trackAmplitude = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteTimeDomainData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const val = (dataArray[i] - 128) / 128;
          sum += val * val;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        setAmplitude(rms);

        if (state === 'Listening') {
          requestAnimationFrame(trackAmplitude);
        }
      };
      trackAmplitude();

    } catch (err) {
      console.error('Error accessing microphone:', err);
      setState('Idle');
    }
  };

  const stopListening = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: 'stop_listening' }));
    streamRef.current?.getTracks().forEach(t => t.stop());
    setState('Idle');
  }, []);

  const playAudioChunk = async (base64Audio: string) => {
    if (!audioContextRef.current) return;

    const arrayBuffer = Uint8Array.from(atob(base64Audio), c => c.charCodeAt(0)).buffer;
    const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContextRef.current.destination);
    source.start();
  };

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      streamRef.current?.getTracks().forEach(t => t.stop());
    };
  }, [connect]);

  return {
    state,
    amplitude,
    startListening,
    stopListening,
    setState // Allow manual state overrides for testing
  };
}
