import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Play, Pause, Loader2 } from 'lucide-react';

export const QuestionSpeaker = ({ text, autoPlay = false }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setSupported(true);
    }
  }, []);

  useEffect(() => {
    if (autoPlay && supported && text) {
      handleSpeak();
    }
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [text, autoPlay, supported]);

  const handleSpeak = () => {
    if (!supported || !text) return;

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      return;
    }

    window.speechSynthesis.cancel(); // Stop any pending speech

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Pick a natural English voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(
      (v) => (v.lang.startsWith('en') && v.name.includes('Natural')) || v.name.includes('Google') || v.name.includes('Samantha')
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.onstart = () => setIsPlaying(true);
    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = () => setIsPlaying(false);

    window.speechSynthesis.speak(utterance);
  };

  if (!supported) return null;

  return (
    <button
      type="button"
      onClick={handleSpeak}
      className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
        isPlaying
          ? 'bg-brand-500/20 text-brand-400 border border-brand-500/40 animate-pulse'
          : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60'
      }`}
      title={isPlaying ? 'Stop Voice Playback' : 'Listen to Question Spoken by AI Interviewer'}
    >
      {isPlaying ? (
        <>
          <VolumeX className="w-3.5 h-3.5 text-brand-400" />
          <span>Stop Voice</span>
        </>
      ) : (
        <>
          <Volume2 className="w-3.5 h-3.5 text-slate-400 group-hover:text-white" />
          <span>Listen</span>
        </>
      )}
    </button>
  );
};
