import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Square, RefreshCw, Loader2, Volume2 } from 'lucide-react';
import { speechApi } from '../api/speech';

export const AudioRecorder = ({ onTranscriptChange, isRecording, setIsRecording }) => {
  const [seconds, setSeconds] = useState(0);
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [speechRecSupported, setSpeechRecSupported] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const timerIntervalRef = useRef(null);

  // Setup Web Speech API recognition for instant live transcription
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSpeechRecSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript + ' ';
        }
        if (transcript.trim()) {
          onTranscriptChange(transcript.trim());
        }
      };

      recognition.onerror = (e) => {
        console.warn('Speech recognition notice:', e.error);
      };

      recognitionRef.current = recognition;
    }
  }, [onTranscriptChange]);

  // Handle Recording Toggle
  useEffect(() => {
    if (isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
    return () => {
      stopRecording();
    };
  }, [isRecording]);

  const startRecording = async () => {
    audioChunksRef.current = [];
    setSeconds(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Setup audio level analyzer for waveform animation
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
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          const avg = sum / dataArray.length;
          setVolumeLevel(avg);
          animationFrameRef.current = requestAnimationFrame(updateVolume);
        };
        updateVolume();
      } catch (err) {
        console.warn('Audio analyzer initialization issue:', err);
      }

      // Setup MediaRecorder
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop stream tracks
        stream.getTracks().forEach((track) => track.stop());

        // Process recorded audio blob if speech recognition was not available or empty
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (audioBlob.size > 0 && !speechRecSupported) {
          try {
            setProcessing(true);
            const res = await speechApi.transcribeAudio(audioBlob);
            if (res.transcription) {
              onTranscriptChange(res.transcription);
            }
          } catch (e) {
            console.error('Transcription error:', e);
          } finally {
            setProcessing(false);
          }
        }
      };

      mediaRecorder.start(250); // Record in 250ms chunks

      // Start Web Speech recognition if supported
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          // May already be running
        }
      }

      // Start live timer
      timerIntervalRef.current = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied or unavailable:', err);
      setIsRecording(false);
    }
  };

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
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    setVolumeLevel(0);
  };

  const formatTimer = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isRecording && !processing) return null;

  return (
    <div className="bg-slate-950/90 border border-red-500/30 rounded-xl p-3 flex items-center justify-between text-xs mb-3 animate-fade-in">
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
          <span className="font-semibold text-red-400">
            {processing ? 'Processing Audio...' : 'Recording Voice...'}
          </span>
        </div>

        <span className="font-mono text-slate-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
          {formatTimer(seconds)}
        </span>

        {/* Live Audio Level Waveform Indicator */}
        <div className="flex items-center space-x-1 h-4">
          {[...Array(8)].map((_, i) => {
            const height = Math.max(4, Math.min(16, (volumeLevel / 128) * (16 - (i % 3) * 2)));
            return (
              <div
                key={i}
                className="w-1 bg-red-400 rounded-full transition-all duration-75"
                style={{ height: `${height}px` }}
              />
            );
          })}
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <button
          type="button"
          onClick={() => setIsRecording(false)}
          className="inline-flex items-center space-x-1 px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg border border-red-500/30 font-medium transition-colors"
        >
          <Square className="w-3.5 h-3.5" />
          <span>Stop Recording</span>
        </button>
      </div>
    </div>
  );
};
