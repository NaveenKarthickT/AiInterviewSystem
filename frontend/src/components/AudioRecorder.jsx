import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, Square, Loader2, AlertTriangle, CheckCircle2, X } from 'lucide-react';
import { speechApi } from '../api/speech';

/**
 * AudioRecorder
 * Props:
 *   isRecording       – boolean controlled by parent
 *   setIsRecording    – setter to let this component stop itself (mic denied, etc.)
 *   onTranscriptChange – called with the final/live transcribed text
 */
export const AudioRecorder = ({ onTranscriptChange, isRecording, setIsRecording }) => {
  const [seconds, setSeconds] = useState(0);
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [liveText, setLiveText] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const mediaRecorderRef    = useRef(null);
  const audioChunksRef      = useRef([]);
  const recognitionRef      = useRef(null);
  const animationFrameRef   = useRef(null);
  const audioContextRef     = useRef(null);
  const timerIntervalRef    = useRef(null);
  const liveTranscriptRef   = useRef('');
  const streamRef           = useRef(null);
  const errorDismissRef     = useRef(null);

  // ── Web Speech API setup (browser live transcript) ─────────────────────────
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous     = true;
    recognition.interimResults = true;
    recognition.lang           = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let finalText = '';
      let interimText = '';
      for (let i = 0; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalText += event.results[i][0].transcript + ' ';
        } else {
          interimText += event.results[i][0].transcript;
        }
      }
      const combined = (finalText + interimText).trim();
      liveTranscriptRef.current = finalText.trim();
      if (combined) {
        setLiveText(combined);
        onTranscriptChange(finalText.trim() || combined);
      }
    };

    recognition.onerror = (e) => {
      // 'no-speech', 'aborted', 'network' are common non-fatal errors
      if (!['no-speech', 'aborted', 'network'].includes(e.error)) {
        console.warn('Web Speech recognition error:', e.error);
      }
    };

    // Auto-restart on end so it stays alive while recording
    recognition.onend = () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { recognition.start(); } catch (_) {}
      }
    };

    recognitionRef.current = recognition;

    return () => {
      try { recognition.stop(); } catch (_) {}
    };
  }, [onTranscriptChange]);

  // ── Trigger start/stop when parent flips isRecording ───────────────────────
  useEffect(() => {
    if (isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
    // cleanup on unmount
    return () => { stopRecording(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRecording]);

  // ── Auto-dismiss error/success after 10 seconds ────────────────────────────
  const showError = useCallback((msg) => {
    setErrorMsg(msg);
    if (errorDismissRef.current) clearTimeout(errorDismissRef.current);
    errorDismissRef.current = setTimeout(() => setErrorMsg(''), 10000);
  }, []);

  const showSuccess = useCallback((msg) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(''), 5000);
  }, []);

  // ── Start recording ─────────────────────────────────────────────────────────
  const startRecording = async () => {
    audioChunksRef.current = [];
    liveTranscriptRef.current = '';
    setLiveText('');
    setErrorMsg('');
    setSuccessMsg('');
    setSeconds(0);

    // Request mic permission
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      streamRef.current = stream;
    } catch (err) {
      const msg = err.name === 'NotAllowedError'
        ? 'Microphone access was denied. Please allow microphone permission in your browser settings and try again.'
        : `Could not access microphone: ${err.message}`;
      showError(msg);
      setIsRecording(false);
      return;
    }

    // Audio level visualizer
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const audioCtx    = new AudioContext();
      audioContextRef.current = audioCtx;
      const source  = audioCtx.createMediaStreamSource(stream);
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
    } catch (_) {}

    // Detect best supported audio MIME type
    const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
      .find((t) => MediaRecorder.isTypeSupported(t)) || '';

    const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    mediaRecorderRef.current = mediaRecorder;

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      // Stop all tracks
      stream.getTracks().forEach((t) => t.stop());

      const webSpeechText = liveTranscriptRef.current.trim();

      if (webSpeechText) {
        // Web Speech already populated the textarea — just show success
        onTranscriptChange(webSpeechText);
        showSuccess('Voice transcribed successfully!');
        return;
      }

      // Fallback: send audio blob to backend STT
      const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });

      if (audioBlob.size < 1000) {
        showError('Recording was too short or empty. Please speak clearly and try again.');
        return;
      }

      setProcessing(true);
      try {
        const ext = (mimeType || 'audio/webm').split('/')[1]?.split(';')[0] || 'webm';
        const res = await speechApi.transcribeAudio(audioBlob, `recording.${ext}`);
        const backendText = (res.transcription || '').trim();

        if (backendText && !backendText.startsWith('[Audio Response Recorded')) {
          onTranscriptChange(backendText);
          setLiveText(backendText);
          showSuccess('Voice transcribed successfully!');
        } else {
          // Backend has no STT configured (no Gemini/OpenAI key on server)
          showError(
            'Voice transcription is not available on the server. Please type your answer in the text box below.'
          );
        }
      } catch (e) {
        console.error('Backend transcription error:', e);
        const status = e?.response?.status;
        if (status === 401 || status === 403) {
          showError('Authentication error. Please refresh and log in again.');
        } else if (status === 413) {
          showError('Recording was too large. Please record a shorter answer.');
        } else {
          showError('Voice transcription failed. Please type your answer below.');
        }
      } finally {
        setProcessing(false);
      }
    };

    mediaRecorder.start(250); // collect chunks every 250ms

    // Start Web Speech live recognition
    if (recognitionRef.current) {
      try { recognitionRef.current.start(); } catch (_) {}
    }

    // Timer
    timerIntervalRef.current = setInterval(() => {
      setSeconds((s) => s + 1);
    }, 1000);
  };

  // ── Stop recording ──────────────────────────────────────────────────────────
  const stopRecording = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (_) {}
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setVolumeLevel(0);
  };

  const formatTimer = (s) => {
    const m = Math.floor(s / 60);
    return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  };

  // ── Don't render anything when idle and no message ─────────────────────────
  if (!isRecording && !processing && !errorMsg && !successMsg) return null;

  return (
    <div className="rounded-xl border border-slate-800 mb-3 overflow-hidden text-xs">
      {/* Recording bar */}
      {(isRecording || processing) && (
        <div className="bg-slate-950/90 border-b border-slate-800 px-3 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {processing ? (
              <Loader2 className="w-3.5 h-3.5 text-brand-400 animate-spin" />
            ) : (
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping flex-shrink-0" />
            )}
            <span className={`font-semibold ${processing ? 'text-brand-400' : 'text-red-400'}`}>
              {processing ? 'Transcribing audio...' : 'Recording Voice...'}
            </span>

            {!processing && (
              <span className="font-mono text-slate-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                {formatTimer(seconds)}
              </span>
            )}

            {/* Waveform visualizer */}
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
          <p className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider mb-1">
            Live Transcript Preview
          </p>
          <p className="text-slate-200 leading-relaxed">{liveText}</p>
        </div>
      )}

      {/* Success message */}
      {successMsg && !processing && (
        <div className="bg-emerald-500/10 border-b border-emerald-500/20 px-3 py-2 flex items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
            <span className="text-emerald-300 font-medium">{successMsg}</span>
          </div>
          <button
            type="button"
            onClick={() => setSuccessMsg('')}
            className="text-emerald-400 hover:text-emerald-300 flex-shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Error message */}
      {errorMsg && !processing && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-3 py-2 flex items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span className="text-amber-300 font-medium">{errorMsg}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMsg('')}
            className="text-amber-400 hover:text-amber-300 flex-shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
};
