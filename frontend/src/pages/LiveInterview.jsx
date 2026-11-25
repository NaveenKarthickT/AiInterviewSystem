import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { interviewApi } from '../api/interview';
import { DualScoreBadge } from '../components/DualScoreBadge';
import { QuestionSpeaker } from '../components/QuestionSpeaker';
import { AudioRecorder } from '../components/AudioRecorder';
import {
  Send,
  Mic,
  MicOff,
  BrainCircuit,
  Award,
  Layers,
  Sparkles,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  Loader2,
  Clock,
  Briefcase,
  Sliders,
  Volume2,
} from 'lucide-react';

export const LiveInterview = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [session, setSession] = useState(null);
  const [turns, setTurns] = useState([]);
  const [currentTurn, setCurrentTurn] = useState(null);
  const [candidateAnswer, setCandidateAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [turnEvaluations, setTurnEvaluations] = useState({});
  const [isRecording, setIsRecording] = useState(false);
  const [autoPlayVoice, setAutoPlayVoice] = useState(false);

  const turnsEndRef = useRef(null);

  const stageLabels = {
    intro: '1. Introduction',
    skill_verification: '2. Skill Verification',
    technical: '3. Technical Questions',
    problem_solving: '4. Problem Solving',
    project_discussion: '5. Project Deep Dive',
    experience_discussion: '6. Internship & Experience',
    behavioral_hr: '7. Behavioral & HR',
  };

  const stageKeys = [
    'intro',
    'skill_verification',
    'technical',
    'problem_solving',
    'project_discussion',
    'experience_discussion',
    'behavioral_hr',
  ];

  const loadSessionData = async () => {
    try {
      setLoading(true);
      const data = await interviewApi.getSession(sessionId);
      setSession(data);
      setTurns(data.turns || []);

      if (data.interaction_mode === 'voice') {
        setAutoPlayVoice(true);
      }

      // Find currently pending turn
      const pending = (data.turns || []).find((t) => !t.candidate_answer);
      setCurrentTurn(pending || null);

      // Load evaluations for completed turns
      const evals = {};
      for (const t of data.turns || []) {
        if (t.candidate_answer) {
          try {
            const ev = await interviewApi.getTurnEvaluation(sessionId, t.id);
            evals[t.id] = ev;
          } catch (e) {}
        }
      }
      setTurnEvaluations(evals);
    } catch (err) {
      console.error(err);
      setError('Failed to load interview session.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessionData();
  }, [sessionId]);

  useEffect(() => {
    turnsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, submitting]);

  const handleSubmitAnswer = async (e) => {
    e?.preventDefault();
    if (!candidateAnswer.trim() || !currentTurn || submitting) return;

    if (isRecording) {
      setIsRecording(false);
    }

    try {
      setError('');
      setSubmitting(true);

      const res = await interviewApi.submitAnswer(sessionId, currentTurn.id, candidateAnswer.trim());

      setTurnEvaluations((prev) => ({
        ...prev,
        [currentTurn.id]: res.evaluation,
      }));

      setTurns((prev) =>
        prev.map((t) => (t.id === currentTurn.id ? res.turn : t))
      );

      if (res.next_turn) {
        setTurns((prev) => [...prev, res.next_turn]);
        setCurrentTurn(res.next_turn);
      } else {
        setCurrentTurn(null);
      }

      setCandidateAnswer('');
      const updatedSession = await interviewApi.getSession(sessionId);
      setSession(updatedSession);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to submit response.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTranscriptStream = (text) => {
    setCandidateAnswer(text);
  };

  const getDifficultyBadge = (diff) => {
    switch (diff?.toLowerCase()) {
      case 'advanced':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'basic':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      default:
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
          <p className="text-slate-400 text-sm">Preparing interview environment...</p>
        </div>
      </div>
    );
  }

  const isCompleted = session?.status === 'completed' || !currentTurn;
  const currentStageIndex = stageKeys.indexOf(session?.current_stage || 'intro');

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Session Status Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-bold text-white">{session?.job_role}</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60 font-medium capitalize">
              {session?.experience_level?.replace('_', ' ')}
            </span>
            {session?.interview_type === 'topic' ? (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-semibold">
                Topic: {session?.focus_topic || 'Specialized'}
              </span>
            ) : session?.interview_type === 'role' ? (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 font-semibold">
                Role-Based
              </span>
            ) : (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/20 font-semibold">
                Resume-Based
              </span>
            )}
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 capitalize font-medium">
              {session?.interaction_mode} Mode
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 flex items-center space-x-2">
            <span>Stage {currentStageIndex + 1} of 7:</span>
            <span className="text-brand-400 font-semibold">
              {stageLabels[session?.current_stage] || session?.current_stage}
            </span>
          </p>
        </div>

        {/* Right Actions: Auto-play Voice Toggle & Dual Averages */}
        <div className="flex items-center space-x-4">
          <label className="hidden sm:flex items-center space-x-2 text-xs text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoPlayVoice}
              onChange={(e) => setAutoPlayVoice(e.target.checked)}
              className="rounded bg-slate-950 border-slate-700 text-brand-500 focus:ring-brand-500"
            />
            <span>Auto-read questions</span>
          </label>

          <div className="flex items-center space-x-4 bg-slate-950/60 px-4 py-2 rounded-xl border border-slate-800/80">
            <div className="flex items-center space-x-2">
              <Award className="w-4 h-4 text-indigo-400" />
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                  Tech Avg
                </span>
                <span className="text-sm font-bold text-white">
                  {session?.avg_knowledge_score ? `${session.avg_knowledge_score}%` : '--'}
                </span>
              </div>
            </div>

            <div className="h-6 w-px bg-slate-800" />

            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-amber-400" />
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                  Comm Avg
                </span>
                <span className="text-sm font-bold text-white">
                  {session?.avg_comm_score ? `${session.avg_comm_score}%` : '--'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 7-Stage Visual Progress Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 mb-6 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[600px] gap-2">
          {stageKeys.map((stKey, idx) => {
            const isPassed = idx < currentStageIndex;
            const isCurrent = idx === currentStageIndex;
            return (
              <div key={stKey} className="flex-1 flex items-center">
                <div className="flex items-center space-x-2">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                      isPassed
                        ? 'bg-emerald-500 text-slate-950'
                        : isCurrent
                        ? 'bg-brand-500 text-white ring-4 ring-brand-500/20'
                        : 'bg-slate-800 text-slate-500'
                    }`}
                  >
                    {isPassed ? <CheckCircle2 className="w-3.5 h-3.5" /> : idx + 1}
                  </div>
                  <span
                    className={`text-xs font-medium truncate max-w-[90px] ${
                      isCurrent ? 'text-white font-bold' : isPassed ? 'text-slate-300' : 'text-slate-500'
                    }`}
                  >
                    {stKey.replace('_', ' ')}
                  </span>
                </div>
                {idx < stageKeys.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-2 rounded ${
                      isPassed ? 'bg-emerald-500/50' : 'bg-slate-800'
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Conversational Stream */}
      <div className="space-y-6 mb-8">
        {turns.map((turn, index) => {
          const evalResult = turnEvaluations[turn.id];
          const isLatest = index === turns.length - 1;

          return (
            <div key={turn.id} className="space-y-4">
              {/* Interviewer Question Card */}
              <div className="flex items-start space-x-3.5">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center flex-shrink-0 shadow-md shadow-brand-500/20">
                  <BrainCircuit className="w-5 h-5 text-white" />
                </div>

                <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2 pb-2 border-b border-slate-800/60">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-brand-400">
                        Turn #{turn.turn_number}
                      </span>
                      <span className="text-xs text-slate-500">•</span>
                      <span className="text-xs font-semibold text-slate-300">
                        {stageLabels[turn.stage] || turn.stage}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <QuestionSpeaker
                        text={turn.question_text}
                        autoPlay={isLatest && autoPlayVoice}
                      />
                      <span
                        className={`text-[11px] font-semibold px-2 py-0.5 rounded border capitalize ${getDifficultyBadge(
                          turn.difficulty_level
                        )}`}
                      >
                        {turn.difficulty_level}
                      </span>
                    </div>
                  </div>

                  <p className="text-base text-slate-100 font-medium leading-relaxed">
                    {turn.question_text}
                  </p>

                  {/* Context Rationale */}
                  {turn.context_rationale && (
                    <div className="mt-3 text-xs text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 flex items-start space-x-2">
                      <HelpCircle className="w-3.5 h-3.5 text-brand-400 flex-shrink-0 mt-0.5" />
                      <span>{turn.context_rationale}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Candidate Response Card (if already answered) */}
              {turn.candidate_answer && (
                <div className="flex items-start justify-end space-x-3.5 pl-8 sm:pl-16">
                  <div className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl p-5">
                    <span className="text-xs font-bold text-slate-400 block mb-1">
                      Your Response
                    </span>
                    <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                      {turn.candidate_answer}
                    </p>

                    {/* Dual Score Evaluation Badge */}
                    <DualScoreBadge evaluation={evalResult} />
                  </div>
                </div>
              )}
            </div>
          );
        })}

        <div ref={turnsEndRef} />
      </div>

      {/* Response Box or Completion Card */}
      {isCompleted ? (
        <div className="bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 border border-brand-500/30 rounded-2xl p-8 text-center shadow-2xl">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-white">Interview Session Completed!</h2>
          <p className="text-slate-300 text-sm mt-2 max-w-xl mx-auto">
            You've completed all stages. The AI analytics engine has processed your dual evaluations,
            identified core knowledge gaps, and prepared your personalized report.
          </p>

          <div className="mt-6 flex flex-wrap justify-center gap-4">
            <button
              onClick={() => navigate(`/reports/${sessionId}`)}
              className="inline-flex items-center space-x-2 bg-brand-600 hover:bg-brand-500 text-white font-medium px-6 py-3 rounded-xl shadow-lg shadow-brand-500/25 transition-all text-sm group"
            >
              <span>View Full Analytics & Gap Report</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <Link
              to="/dashboard"
              className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium px-6 py-3 rounded-xl border border-slate-700 transition-all text-sm"
            >
              <span>Back to Dashboard</span>
            </Link>
          </div>
        </div>
      ) : (
        /* Candidate Response Input Bar */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl sticky bottom-4 z-40">
          {/* Live Audio Recorder Panel */}
          <AudioRecorder
            isRecording={isRecording}
            setIsRecording={setIsRecording}
            onTranscriptChange={handleTranscriptStream}
          />

          <form onSubmit={handleSubmitAnswer} className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="font-semibold text-slate-300 flex items-center space-x-1.5">
                <span>Answering Turn #{currentTurn?.turn_number}</span>
                <span className="text-slate-500">•</span>
                <span className="text-brand-400">{currentTurn?.stage}</span>
              </span>
              <span>{candidateAnswer.length} characters</span>
            </div>

            <textarea
              rows={4}
              required
              value={candidateAnswer}
              onChange={(e) => setCandidateAnswer(e.target.value)}
              placeholder="Speak using the microphone or type your answer here (explain principles, trade-offs, and examples)..."
              className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl p-3.5 text-sm text-slate-100 placeholder-slate-600 outline-none resize-none transition-all"
            />

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center space-x-2 text-xs text-slate-500">
                <Sparkles className="w-3.5 h-3.5 text-brand-400" />
                <span>Technical knowledge and communication are evaluated independently</span>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={() => setIsRecording(!isRecording)}
                  className={`inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl border transition-all text-xs font-semibold ${
                    isRecording
                      ? 'bg-red-500/20 text-red-400 border-red-500 animate-pulse'
                      : 'bg-slate-800 text-slate-300 border-slate-700 hover:text-white hover:bg-slate-700'
                  }`}
                  title={isRecording ? 'Stop Recording' : 'Record Voice Answer'}
                >
                  {isRecording ? (
                    <>
                      <MicOff className="w-4 h-4 text-red-400" />
                      <span>Recording...</span>
                    </>
                  ) : (
                    <>
                      <Mic className="w-4 h-4 text-brand-400" />
                      <span>Speak Answer</span>
                    </>
                  )}
                </button>

                <button
                  type="submit"
                  disabled={submitting || !candidateAnswer.trim()}
                  className="inline-flex items-center space-x-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-medium px-6 py-2.5 rounded-xl shadow-md shadow-brand-500/25 transition-all text-sm group"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Evaluating Answer...</span>
                    </>
                  ) : (
                    <>
                      <span>Submit Answer</span>
                      <Send className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
