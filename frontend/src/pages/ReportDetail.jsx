import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { reportApi } from '../api/report';
import { RadarChart } from '../components/RadarChart';
import {
  Award,
  Layers,
  Sparkles,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  BrainCircuit,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Download,
  Loader2,
} from 'lucide-react';

export const ReportDetail = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        const data = await reportApi.getReport(sessionId);
        setReport(data);
      } catch (err) {
        console.error(err);
        setError('Failed to load performance report.');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [sessionId]);

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/15 text-red-400 border-red-500/30';
      case 'moderate':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      default:
        return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
          <p className="text-slate-400 text-sm">Synthesizing full performance report & gap analytics...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="w-12 h-12 rounded-2xl bg-red-500/10 text-red-400 flex items-center justify-center mx-auto mb-4 border border-red-500/20">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-white">Report Not Found</h2>
        <p className="text-sm text-slate-400 mt-1">{error || 'Session report could not be generated.'}</p>
        <Link
          to="/dashboard"
          className="mt-6 inline-flex items-center space-x-2 bg-brand-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold"
        >
          <span>Return to Dashboard</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 border border-slate-800 rounded-3xl p-8 mb-8 shadow-2xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold mb-3">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Dual-Perspective Evaluation Analytics</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Performance & Knowledge Gap Analysis
            </h1>
            <p className="text-slate-300 text-sm mt-1">
              Target Role: <strong className="text-white">{report.job_role}</strong> ({report.experience_level}) • Session Completed on {new Date(report.created_at).toLocaleDateString()}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to={`/optimizer?sessionId=${report.session_id}`}
              className="inline-flex items-center space-x-2 bg-brand-600 hover:bg-brand-500 text-white font-medium px-5 py-2.5 rounded-xl shadow-lg shadow-brand-500/25 transition-all text-sm group"
            >
              <Sparkles className="w-4 h-4" />
              <span>Optimize Resume with Evidence</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </div>

      {/* Dual Scores Hero Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Technical Knowledge Score */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Technical Knowledge Score</h3>
                <p className="text-xs text-slate-400">Strict technical correctness & depth</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-3xl font-extrabold text-indigo-400">
                {report.overall_knowledge_score}%
              </span>
            </div>
          </div>

          <div className="w-full bg-slate-950 rounded-full h-2.5 mb-4 border border-slate-800 overflow-hidden">
            <div
              className="bg-gradient-to-r from-indigo-500 to-brand-500 h-2.5 rounded-full transition-all duration-1000"
              style={{ width: `${Math.min(report.overall_knowledge_score, 100)}%` }}
            />
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluated strictly on conceptual accuracy, internal mechanics, and real-world trade-off analysis. Never reduced for accents, grammar, or vocabulary.
          </p>
        </div>

        {/* Communication Score */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Communication Delivery Score</h3>
                <p className="text-xs text-slate-400">Clarity, structure & articulation</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-3xl font-extrabold text-amber-400">
                {report.overall_comm_score}%
              </span>
            </div>
          </div>

          <div className="w-full bg-slate-950 rounded-full h-2.5 mb-4 border border-slate-800 overflow-hidden">
            <div
              className="bg-gradient-to-r from-amber-500 to-yellow-400 h-2.5 rounded-full transition-all duration-1000"
              style={{ width: `${Math.min(report.overall_comm_score, 100)}%` }}
            />
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluated on top-down explanation organization, conciseness, professional vocabulary, and coherent grammar, independent of technical accuracy.
          </p>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
          <BrainCircuit className="w-4 h-4 text-brand-400" />
          <span>Executive Hiring Synthesis</span>
        </h3>
        <p className="text-sm text-slate-200 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          {report.executive_summary}
        </p>
      </div>

      {/* Radar Chart & Verified Skills */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
        {/* Radar Chart */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2 mb-1">
              <BarChart3 className="w-4 h-4 text-brand-400" />
              <span>Engineering Competency Radar</span>
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Visualizes candidate proficiency vs standard industry hiring benchmark across 6 core dimensions.
            </p>
          </div>
          <RadarChart data={report.radar_metrics} />
        </div>

        {/* Verified Skills Column */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2 mb-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Interview-Verified Skills ({report.verified_skills?.length || 0})</span>
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Competencies substantiated with strong technical answers and architectural defense.
            </p>

            <div className="flex flex-wrap gap-2">
              {(report.verified_skills || []).map((skill, idx) => (
                <span
                  key={idx}
                  className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-300 border border-emerald-500/25 flex items-center space-x-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{skill}</span>
                </span>
              ))}
            </div>
          </div>

          <div className="mt-6 p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <p className="text-xs text-slate-400 leading-snug">
              These verified competencies will be highlighted on your optimized ATS resume in Phase 8.
            </p>
          </div>
        </div>
      </div>

      {/* Stage-by-Stage Performance Breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
        <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-blue-400" />
          <span>7-Stage Recruitment Performance Breakdown</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(report.stage_breakdown || []).map((st, idx) => (
            <div
              key={idx}
              className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between"
            >
              <div>
                <p className="text-xs font-bold text-white truncate mb-2">{st.stage_title}</p>
                <div className="space-y-2 text-xs">
                  <div>
                    <div className="flex justify-between text-slate-400 mb-1">
                      <span>Technical Score:</span>
                      <span className="font-semibold text-indigo-400">{st.knowledge_score}%</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-indigo-500 h-1.5 rounded-full"
                        style={{ width: `${st.knowledge_score}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-slate-400 mb-1">
                      <span>Delivery Score:</span>
                      <span className="font-semibold text-amber-400">{st.comm_score}%</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-amber-400 h-1.5 rounded-full"
                        style={{ width: `${st.comm_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-slate-500 mt-3 pt-2 border-t border-slate-800/60">
                {st.turns_count} question(s) evaluated
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Knowledge Gaps Matrix */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
        <h3 className="text-base font-bold text-white mb-2 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <span>Identified Technical Knowledge Gaps ({report.knowledge_gaps?.length || 0})</span>
        </h3>
        <p className="text-xs text-slate-400 mb-5">
          Specific architectural concepts, edge cases, or trade-offs omitted or under-explained during the interview.
        </p>

        <div className="space-y-3.5">
          {(report.knowledge_gaps || []).map((gap, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col md:flex-row md:items-start justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center space-x-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${getSeverityBadge(gap.severity)}`}>
                    {gap.severity} Priority
                  </span>
                  <h4 className="text-sm font-bold text-white">{gap.topic}</h4>
                </div>
                <p className="text-xs text-slate-400 italic">
                  "{gap.evidence_quote}"
                </p>
                <p className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-2.5 rounded-lg mt-2">
                  <strong className="text-emerald-300">Targeted Remedy:</strong> {gap.remedy_recommendation}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Personalized Learning Plan */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-base font-bold text-white mb-2 flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-brand-400" />
          <span>Personalized Engineering Learning Plan</span>
        </h3>
        <p className="text-xs text-slate-400 mb-5">
          Actionable coding and system design tasks tailored to close your identified gaps before real recruitment loops.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {(report.personalized_learning_plan || []).map((plan, idx) => (
            <div
              key={idx}
              className="bg-slate-950/70 border border-slate-800 rounded-xl p-5 flex flex-col justify-between"
            >
              <div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-brand-500/15 text-brand-400 border border-brand-500/20 uppercase">
                  {plan.category}
                </span>
                <h4 className="text-sm font-bold text-white mt-2 mb-2">{plan.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed mb-3">{plan.description}</p>
                
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-400 mb-3">
                  <strong className="text-slate-200 block mb-1">Hands-on Task:</strong>
                  {plan.actionable_exercise}
                </div>
              </div>

              {plan.suggested_reading && (
                <div className="text-[11px] text-brand-400 pt-2 border-t border-slate-800/80">
                  <span className="text-slate-500">Reading:</span> {plan.suggested_reading}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
