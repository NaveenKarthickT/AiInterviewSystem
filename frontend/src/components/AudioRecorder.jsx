import React, { useState, useEffect, useRef } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { speechApi } from '../api/speech';

export const AudioRecorder = ({ onTranscriptChange, isRecording, setIsRecording }) => {
  const [seconds, setSeconds] = useState(0);
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [liveText, setLiveText] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const liveTranscriptRef = useRef(''); // tracks live Web Speech text without stale closure

  // Setup Web Speech API for live preview (best-effort — not all browsers)
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        let finalText = '';
        let interimText = '';
        for (let i = 0; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalText += result[0].transcript + ' ';
          } else {
            interimText += result[0].transcript;
          }
        }
        const combined = (finalText + interimText).trim();
        liveTranscriptRef.current = finalText.trim(); // only save final for submission
        if (combined) {
          setLiveText(combined);
          onTranscriptChange(finalText.trim() || combined); // push live updates
        }
      };

      recognition.onerror = (e) => {
        // 'no-speech' and 'aborted' are expected; don't show error for those
        if (e.error !== 'no-speech' && e.error !== 'aborted') {
          console.warn('Speech recognition error:', e.error);
        }
      };

      recognitionRef.current = recognition;
    }
  }, [onTranscriptChange]);

  // Trigger start/stop when parent flips isRecording
  useEffect(() => {
    if (isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
    return () => stopRecording();
  }, [isRecording]);

  const startRecording = async () => {
    audioChunksRef.current = [];
    liveTranscriptRef.current = '';
    setLiveText('');
    setErrorMsg('');
    setSeconds(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Audio level visualizer
      try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const audioCtx = new AudioContext();
        audioContextRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        source.connect(analyser);
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const updateVolume = () => {
          analyser.getByteFrequencyData(dataArray);
          const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
          setVolumeLevel(avg);
          animationFrameRef.current = requestAnimationFrame(updateVolume);
        };
        updateVolume();
      } catch (e) {
        console.warn('Audio analyser init error:', e);
      }

      // MediaRecorder for audio blob (backend fallback)
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());

        const webSpeechText = liveTranscriptRef.current.trim();

        // Always try backend transcription if Web Speech API gave nothing
        if (!webSpeechText) {
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
          if (audioBlob.size > 500) {
            setProcessing(true);
            try {
              const res = await speechApi.transcribeAudio(audioBlob, `recording.${mimeType.split('/')[1].split(';')[0]}`);
              const backendText = (res.transcription || '').trim();
              if (backendText && !backendText.startsWith('[Audio Response')) {
                onTranscriptChange(backendText);
                setLiveText(backendText);
              } else if (backendText.startsWith('[Audio Response')) {
                // Backend has no STT configured — tell user to type instead
                setErrorMsg("Voice-to-text not available in this environment. Please type your answer below.");
              }
            } catch (e) {
              console.error('Backend transcription failed:', e);
              setErrorMsg("Voice transcription failed. Please type your answer.");
            } finally {
              setProcessing(false);
            }
          } else {
            setErrorMsg("Recording was too short or empty. Please try again.");
          }
        }
        // If webSpeechText already has content, it was pushed to parent in onresult — nothing extra needed
      };

      mediaRecorder.start(250);

      // Start Web Speech live recognition
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) { /* already running */ }
      }

      // Timer
      timerIntervalRef.current = setInterval(() => {
        setSeconds((s) => s + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied:', err);
      setErrorMsg('Microphone access was denied. Please allow microphone permission and try again.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (timerIntervalRef.current) { clearInterval(timerIntervalRef.current); timerIntervalRef.current = null; }
    if (animationFrameRef.current) { cancelAnimationFrame(animationFrameRef.current); animationFrameRef.current = null; }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
    setVolumeLevel(0);
  };

  const formatTimer = (s) => {
    const m = Math.floor(s / 60);
    return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  };

  if (!isRecording && !processing && !errorMsg) return null;

  return (
    <div className="rounded-xl border mb-3 overflow-hidden text-xs">
      {/* Recording bar */}
      {(isRecording || processing) && (
        <div className="bg-slate-950/90 border-b border-slate-800 px-3 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {processing ? (
              <Loader2 className="w-3.5 h-3.5 text-brand-400 animate-spin" />
            ) : (
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
            )}
            <span className={`font-semibold ${processing ? 'text-brand-400' : 'text-red-400'}`}>
              {processing ? 'Transcribing audio...' : 'Recording Voice...'}
            </span>

            {!processing && (
              <span className="font-mono text-slate-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                {formatTimer(seconds)}
              </span>
            )}

            {/* Waveform */}
            {isRecording && !processing && (
              <div className="flex items-center space-x-0.5 h-4">
                {[...Array(8)].map((_, i) => {
                  const h = Math.max(3, Math.min(16, (volumeLevel / 128) * (16 - (i % 3) * 2)));
                  return (
                    <div
                      key={i}
                      className="w-1 bg-red-400 rounded-full transition-all duration-75"
                      style={{ height: `${h}px` }}
                    />
                  );
                })}
              </div>
            )}
          </div>

          {isRecording && !processing && (
            <button
              type="button"
              onClick={() => setIsRecording(false)}
              className="inline-flex items-center space-x-1.5 px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg border border-red-500/30 font-medium transition-colors"
            >
              <Square className="w-3.5 h-3.5" />
              <span>Stop Recording</span>
            </button>
          )}
        </div>
      )}

      {/* Live transcript preview */}
      {isRecording && liveText && (
        <div className="bg-slate-900 px-3 py-2 border-b border-slate-800">
          <p className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider mb-1">Live Transcript Preview</p>
          <p className="text-slate-200 leading-relaxed">{liveText}</p>
        </div>
      )}

      {/* Error message */}
      {errorMsg && !processing && (
        <div className="bg-amber-500/10 border-amber-500/30 border px-3 py-2 flex items-center justify-between gap-2">
          <span className="text-amber-300 font-medium">{errorMsg}</span>
          <button
            type="button"
            onClick={() => setErrorMsg('')}
            className="text-amber-400 hover:text-amber-300 font-bold text-sm flex-shrink-0"
          >✕</button>
        </div>
      )}
    </div>
  );
};
