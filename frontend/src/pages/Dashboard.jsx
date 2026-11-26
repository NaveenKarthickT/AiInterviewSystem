import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { resumeApi } from '../api/resume';
import { interviewApi } from '../api/interview';
import { reportApi } from '../api/report';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts';
import {
  FileText,
  PlayCircle,
  Sparkles,
  BarChart3,
  Award,
  Layers,
  ArrowRight,
  CheckCircle2,
  Clock,
  ShieldCheck,
  List,
  AlertCircle,
  TrendingUp,
  PieChart as PieIcon,
  Target,
  Zap,
} from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Skeleton placeholder for a stat card while loading                 */
/* ------------------------------------------------------------------ */
const StatSkeleton = () => (
  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex items-center space-x-4 animate-pulse">
    <div className="w-12 h-12 rounded-xl bg-slate-800" />
    <div className="flex-1 space-y-2">
      <div className="h-3 w-24 bg-slate-800 rounded" />
      <div className="h-5 w-16 bg-slate-800 rounded" />
    </div>
  </div>
);

/* ------------------------------------------------------------------ */
/*  Skeleton placeholder for an activity row                          */
/* ------------------------------------------------------------------ */
const ActivityRowSkeleton = () => (
  <div className="flex items-center justify-between py-3 animate-pulse">
    <div className="flex-1 space-y-2">
      <div className="h-4 w-40 bg-slate-800 rounded" />
      <div className="h-3 w-24 bg-slate-800 rounded" />
    </div>
    <div className="h-5 w-20 bg-slate-800 rounded-full" />
  </div>
);

/* ------------------------------------------------------------------ */
/*  Status badge component                                            */
/* ------------------------------------------------------------------ */
const StatusBadge = ({ status }) => {
  const isCompleted = status === 'completed';
  return (
    <span
      className={`inline-flex items-center space-x-1 text-xs font-semibold px-2.5 py-0.5 rounded-full ${
        isCompleted
          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
      }`}
    >
      {isCompleted ? (
        <CheckCircle2 className="w-3 h-3" />
      ) : (
        <Clock className="w-3 h-3" />
      )}
      <span>{isCompleted ? 'Completed' : 'In Progress'}</span>
    </span>
  );
};

/* ------------------------------------------------------------------ */
/*  Dashboard component                                               */
/* ------------------------------------------------------------------ */
export const Dashboard = () => {
  const { user } = useAuth();
  const { isDark } = useTheme();

  const [resumes, setResumes] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [resumesData, sessionsData, reportsData] = await Promise.all([
          resumeApi.listResumes(),
          interviewApi.listSessions(),
          reportApi.listReports(),
        ]);
        setResumes(resumesData);
        setSessions(sessionsData);
        setReports(reportsData);
        setLoading(false);
      } catch (e) {
        setError('Failed to load dashboard data');
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const resumeCount = resumes.length;
  const completedSessions = sessions.filter((s) => s.status === 'completed');
  const completedCount = completedSessions.length;

  const reportsArray = Array.isArray(reports) ? reports : [];

  // Only sessions that actually have scores > 0
  const scoredSessions = sessions.filter(
    (s) => (s.avg_knowledge_score != null && s.avg_knowledge_score > 0) ||
            (s.avg_comm_score != null && s.avg_comm_score > 0)
  );

  const knowledgeScores =
    reportsArray.length > 0
      ? reportsArray
          .map((r) => r.knowledge_score ?? r.knowledgeScore ?? null)
          .filter((s) => s !== null && s !== undefined)
      : scoredSessions
          .map((s) => s.avg_knowledge_score)
          .filter((s) => s !== null && s !== undefined && s > 0);

  const communicationScores =
    reportsArray.length > 0
      ? reportsArray
          .map((r) => r.communication_score ?? r.communicationScore ?? r.delivery_score ?? r.deliveryScore ?? null)
          .filter((s) => s !== null && s !== undefined)
      : scoredSessions
          .map((s) => s.avg_comm_score)
          .filter((s) => s !== null && s !== undefined && s > 0);

  const avgKnowledge =
    knowledgeScores.length > 0
      ? Math.round(knowledgeScores.reduce((a, b) => a + b, 0) / knowledgeScores.length)
      : null;
  const avgCommunication =
    communicationScores.length > 0
      ? Math.round(communicationScores.reduce((a, b) => a + b, 0) / communicationScores.length)
      : null;

  const hasAnalyticsData = (scoredSessions.length > 0 && (avgKnowledge !== null || avgCommunication !== null)) || reportsArray.length > 0;

  const computedStats = [
    {
      label: 'Uploaded Resumes',
      value: `${resumeCount} Active`,
      icon: FileText,
      color: 'text-blue-400',
    },
    {
      label: 'Completed Sessions',
      value: `${completedCount} Session${completedCount !== 1 ? 's' : ''}`,
      icon: CheckCircle2,
      color: 'text-emerald-400',
    },
    {
      label: 'Avg Knowledge Score',
      value: avgKnowledge !== null ? `${avgKnowledge} / 100` : '-- / 100',
      icon: Award,
      color: 'text-purple-400',
    },
    {
      label: 'Avg Delivery Score',
      value: avgCommunication !== null ? `${avgCommunication} / 100` : '-- / 100',
      icon: Layers,
      color: 'text-amber-400',
    },
  ];

  /* ---- Chart Data Generation (Real Data Only - Empty State for New Accounts) ---- */
  const performanceTrendData = useMemo(() => {
    if (!hasAnalyticsData) {
      return [];
    }
    return [...scoredSessions]
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      .map((s, idx) => {
        const rep = reportsArray.find((r) => r.session_id === s.id);
        const kScore = rep
          ? (rep.knowledge_score ?? rep.knowledgeScore ?? s.avg_knowledge_score ?? 0)
          : (s.avg_knowledge_score ?? 0);
        const cScore = rep
          ? (rep.communication_score ?? rep.communicationScore ?? s.avg_comm_score ?? 0)
          : (s.avg_comm_score ?? 0);
        return {
          name: `Session ${idx + 1}`,
          role: s.job_role || 'Engineering',
          knowledge: Math.round(kScore),
          communication: Math.round(cScore),
          benchmark: 75,
        };
      });
  }, [hasAnalyticsData, scoredSessions, reportsArray]);

  const readinessBreakdown = useMemo(() => {
    if (!hasAnalyticsData) {
      return [
        { name: 'Technical Depth', value: 0, color: '#6366f1' },
        { name: 'Communication Delivery', value: 0, color: '#10b981' },
        { name: 'Resume Alignment', value: 0, color: '#8b5cf6' },
        { name: 'Problem Solving', value: 0, color: '#f59e0b' },
      ];
    }
    const k = avgKnowledge ?? 0;
    const c = avgCommunication ?? 0;
    return [
      { name: 'Technical Depth', value: k, color: '#6366f1' },
      { name: 'Communication Delivery', value: c, color: '#10b981' },
      { name: 'Resume Alignment', value: resumeCount > 0 ? Math.min(100, Math.round((k * 0.6 + c * 0.4))) : k, color: '#8b5cf6' },
      { name: 'Problem Solving', value: Math.round((k + c) / 2), color: '#f59e0b' },
    ];
  }, [hasAnalyticsData, avgKnowledge, avgCommunication, resumeCount]);

  const compositeReadinessScore = useMemo(() => {
    if (!hasAnalyticsData) return 0;
    const total = readinessBreakdown.reduce((acc, curr) => acc + curr.value, 0);
    return Math.round(total / readinessBreakdown.length);
  }, [hasAnalyticsData, readinessBreakdown]);

  const stageFunnelData = useMemo(() => {
    if (!hasAnalyticsData) {
      return [];
    }
    const k = avgKnowledge ?? 0;
    const c = avgCommunication ?? 0;
    const avg = Math.round((k + c) / 2);
    return [
      { stage: '1. Intro', candidate: c, benchmark: 75 },
      { stage: '2. Skills', candidate: k, benchmark: 75 },
      { stage: '3. Technical', candidate: k, benchmark: 75 },
      { stage: '4. Coding', candidate: avg, benchmark: 75 },
      { stage: '5. Projects', candidate: avg, benchmark: 75 },
      { stage: '6. Exp', candidate: c, benchmark: 75 },
      { stage: '7. HR', candidate: c, benchmark: 75 },
    ];
  }, [hasAnalyticsData, avgKnowledge, avgCommunication]);

  /* Theme-aware chart colors */
  const gridStroke = isDark ? '#1e293b' : '#e2e8f0';
  const axisTickColor = isDark ? '#94a3b8' : '#475569';
  const tooltipBg = isDark ? '#0f172a' : '#ffffff';
  const tooltipBorder = isDark ? '#334155' : '#e2e8f0';
  const tooltipText = isDark ? '#f8fafc' : '#0f172a';

  const recentSessions = [...sessions]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Welcome banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 border border-slate-800 p-8 sm:p-10 mb-10 shadow-2xl transition-all">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold mb-4">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Dual-Perspective Adaptive AI Engine Ready</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Welcome back, {user?.full_name || 'Candidate'}
          </h1>
          <p className="mt-3 text-slate-300 text-base leading-relaxed">
            Practice realistic 7-stage engineering recruitment interviews. Receive independent
            scores for technical depth and communication proficiency, pinpoint knowledge gaps,
            and transform your resume with interview-verified evidence.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              to="/resumes"
              className="inline-flex items-center space-x-2 bg-brand-600 hover:bg-brand-500 text-white font-medium px-5 py-3 rounded-xl shadow-lg shadow-brand-500/25 transition-all group"
            >
              <FileText className="w-5 h-5" />
              <span>Upload &amp; Parse Resume</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              to="/interview/setup"
              className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium px-5 py-3 rounded-xl border border-slate-700 transition-all"
            >
              <PlayCircle className="w-5 h-5 text-brand-400" />
              <span>Start Adaptive Interview</span>
            </Link>
          </div>
        </div>

        {/* Subtle decorative glow */}
        <div className="absolute right-0 top-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-brand-600/10 blur-3xl pointer-events-none" />
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-6 flex items-center space-x-3 rounded-2xl bg-red-500/10 border border-red-500/20 p-4 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        {loading
          ? Array.from({ length: 4 }).map((_, idx) => <StatSkeleton key={idx} />)
          : computedStats.map((stat, idx) => {
              const Icon = stat.icon;
              return (
                <div
                  key={idx}
                  className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex items-center space-x-4 transition-all"
                >
                  <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center flex-shrink-0">
                    <Icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      {stat.label}
                    </p>
                    <p className="text-xl font-bold text-white mt-0.5">{stat.value}</p>
                  </div>
                </div>
              );
            })}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* GRAPHICAL REPRESENTATION: Analytics & Performance Intelligence    */}
      {/* ------------------------------------------------------------------ */}
      <div className="mb-12">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-brand-400" />
              <span>Performance Analytics &amp; Trajectory</span>
            </h2>
            <p className="text-slate-400 text-sm mt-0.5">
              Live dual-perspective tracking of technical depth, delivery clarity, and overall readiness.
            </p>
          </div>
          <span className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20">
            <Zap className="w-3.5 h-3.5" />
            <span>AI Powered Metrics</span>
          </span>
        </div>

        {/* Top Graphical Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Main Trajectory Area Chart (2 Columns on large screens) */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                  <span>Score Trajectory Over Sessions</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Knowledge vs Communication scores against the engineering benchmark
                </p>
              </div>
              <div className="flex items-center space-x-4 text-xs">
                <span className="flex items-center space-x-1.5">
                  <span className="w-3 h-3 rounded-full bg-indigo-500" />
                  <span className="text-slate-300 font-medium">Knowledge</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="text-slate-300 font-medium">Communication</span>
                </span>
              </div>
            </div>

            <div className="w-full h-72 sm:h-80">
              {!hasAnalyticsData ? (
                <div className="h-full flex flex-col items-center justify-center text-center px-4 rounded-2xl border border-dashed border-slate-800 bg-slate-950/40">
                  <BarChart3 className="w-10 h-10 text-slate-600 mb-3" />
                  <p className="text-sm font-semibold text-slate-300">No session scores yet</p>
                  <p className="text-xs text-slate-500 mt-1 max-w-xs">
                    Complete your first mock interview to see your real Knowledge vs. Communication trajectory.
                  </p>
                  <Link
                    to="/interview/setup"
                    className="mt-4 inline-flex items-center space-x-1.5 text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-xl transition-all"
                  >
                    <PlayCircle className="w-4 h-4" />
                    <span>Start First Interview</span>
                  </Link>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={performanceTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="knowledgeGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                      </linearGradient>
                      <linearGradient id="communicationGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                    <XAxis dataKey="name" stroke={axisTickColor} tick={{ fill: axisTickColor, fontSize: 11 }} />
                    <YAxis domain={[0, 100]} stroke={axisTickColor} tick={{ fill: axisTickColor, fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: tooltipBg,
                        borderColor: tooltipBorder,
                        borderRadius: '0.875rem',
                        color: tooltipText,
                        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.15)',
                        fontSize: '12px',
                      }}
                    />
                    <ReferenceLine
                      y={75}
                      stroke="#f59e0b"
                      strokeDasharray="4 4"
                      label={{ value: 'Benchmark (75)', fill: '#f59e0b', fontSize: 10, position: 'top' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="knowledge"
                      name="Knowledge Depth"
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#knowledgeGrad)"
                    />
                    <Area
                      type="monotone"
                      dataKey="communication"
                      name="Communication Score"
                      stroke="#10b981"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#communicationGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Readiness Index Gauge / Donut Chart (1 Column) */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-sm flex flex-col justify-between">
            <div className="mb-2">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <PieIcon className="w-4 h-4 text-emerald-400" />
                <span>Overall Readiness Index</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Composite qualification tier based on 4 pillars
              </p>
            </div>

            {/* Circular Pie Chart with center score */}
            <div className="relative w-full h-52 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  {hasAnalyticsData ? (
                    <Pie
                      data={readinessBreakdown}
                      cx="50%"
                      cy="50%"
                      innerRadius={58}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {readinessBreakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  ) : (
                    <Pie
                      data={[{ name: 'No Data', value: 1 }]}
                      cx="50%"
                      cy="50%"
                      innerRadius={58}
                      outerRadius={80}
                      dataKey="value"
                      isAnimationActive={false}
                    >
                      <Cell fill={isDark ? '#1e293b' : '#e2e8f0'} />
                    </Pie>
                  )}
                  {hasAnalyticsData && (
                    <Tooltip
                      contentStyle={{
                        backgroundColor: tooltipBg,
                        borderColor: tooltipBorder,
                        borderRadius: '0.75rem',
                        color: tooltipText,
                        fontSize: '11px',
                      }}
                    />
                  )}
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-2xl font-black text-white">
                  {hasAnalyticsData ? `${compositeReadinessScore}%` : '--'}
                </span>
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  {hasAnalyticsData ? 'Ready' : 'No Data'}
                </span>
              </div>
            </div>

            {/* Pillar Legend Badges */}
            <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800">
              {readinessBreakdown.map((item, idx) => (
                <div key={idx} className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                  <div className="truncate">
                    <span className="text-xs font-semibold text-slate-200 block truncate">{item.name}</span>
                    <span className="text-[11px] text-slate-400">{hasAnalyticsData ? `${item.value}%` : '--'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 7-Stage Interview Funnel Bar Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
            <div>
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <Target className="w-4 h-4 text-purple-400" />
                <span>7-Stage Interview Competency Breakdown</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluation across all adaptive recruitment stages compared to hiring standard
              </p>
            </div>
            <span className="text-xs font-medium text-slate-400">
              Benchmark Standard: <strong className="text-amber-400">75%</strong>
            </span>
          </div>

          <div className="w-full h-56 sm:h-64">
            {!hasAnalyticsData ? (
              <div className="h-full flex flex-col items-center justify-center text-center px-4 rounded-2xl border border-dashed border-slate-800 bg-slate-950/40">
                <Target className="w-9 h-9 text-slate-600 mb-2.5" />
                <p className="text-sm font-semibold text-slate-300">No stage data available yet</p>
                <p className="text-xs text-slate-500 mt-1">
                  Your 7-stage competency breakdown will appear here after you complete an interview.
                </p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stageFunnelData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                  <XAxis dataKey="stage" stroke={axisTickColor} tick={{ fill: axisTickColor, fontSize: 11 }} />
                  <YAxis domain={[0, 100]} stroke={axisTickColor} tick={{ fill: axisTickColor, fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: tooltipBg,
                      borderColor: tooltipBorder,
                      borderRadius: '0.75rem',
                      color: tooltipText,
                      fontSize: '12px',
                    }}
                  />
                  <ReferenceLine y={75} stroke="#f59e0b" strokeDasharray="3 3" />
                  <Bar dataKey="candidate" name="Candidate Score" fill="#818cf8" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Main Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Card 1: Resume Upload */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4">
              <FileText className="w-5 h-5 text-blue-400" />
            </div>
            <h3 className="text-lg font-bold text-white">1. Resume Analysis</h3>
            <p className="text-slate-400 text-sm mt-2 leading-relaxed">
              Upload your PDF or DOCX resume. The multi-agent parser extracts technical skills,
              experience tiers, and project architectures automatically.
            </p>
          </div>
          <Link
            to="/resumes"
            className="mt-6 inline-flex items-center space-x-2 text-sm font-semibold text-brand-400 hover:text-brand-300"
          >
            <span>Manage Resumes</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Card 2: Adaptive Interview */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-4">
              <PlayCircle className="w-5 h-5 text-purple-400" />
            </div>
            <h3 className="text-lg font-bold text-white">2. Adaptive Mock Session</h3>
            <p className="text-slate-400 text-sm mt-2 leading-relaxed">
              Experience dynamic 7-stage interviews. The engine adjusts difficulty in real time,
              probes incomplete responses, and evaluates via voice or text.
            </p>
          </div>
          <Link
            to="/interview/setup"
            className="mt-6 inline-flex items-center space-x-2 text-sm font-semibold text-brand-400 hover:text-brand-300"
          >
            <span>Configure Interview</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Card 3: Intelligent Resume Optimizer */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4">
              <Sparkles className="w-5 h-5 text-emerald-400" />
            </div>
            <h3 className="text-lg font-bold text-white">3. Intelligent Resume Optimizer</h3>
            <p className="text-slate-400 text-sm mt-2 leading-relaxed">
              Align resume claims with interview-verified competencies. Review Keep / Modify / Verify / Remove
              recommendations and export ATS PDF/DOCX.
            </p>
          </div>
          <Link
            to="/optimizer"
            className="mt-6 inline-flex items-center space-x-2 text-sm font-semibold text-brand-400 hover:text-brand-300"
          >
            <span>Open Optimizer</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="mt-12 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Clock className="w-5 h-5 text-brand-400" />
            <span>Recent Activity</span>
          </h2>
          <Link
            to="/interview/setup"
            className="inline-flex items-center space-x-1.5 text-sm font-semibold text-brand-400 hover:text-brand-300 transition-colors"
          >
            <List className="w-4 h-4" />
            <span>New Interview</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="divide-y divide-slate-800">
            {Array.from({ length: 3 }).map((_, idx) => (
              <ActivityRowSkeleton key={idx} />
            ))}
          </div>
        ) : recentSessions.length === 0 ? (
          <div className="text-center py-8">
            <PlayCircle className="w-10 h-10 text-slate-700 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No interview sessions yet.</p>
            <Link
              to="/interview/setup"
              className="mt-3 inline-flex items-center space-x-1.5 text-sm font-semibold text-brand-400 hover:text-brand-300"
            >
              <span>Start your first interview</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {recentSessions.map((session) => {
              const isCompleted = session.status === 'completed';
              const href = isCompleted
                ? `/reports/${session.id}`
                : `/interview/live/${session.id}`;

              return (
                <Link
                  key={session.id}
                  to={href}
                  className="flex items-center justify-between py-3 group hover:bg-slate-800/40 -mx-2 px-2 rounded-lg transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-white truncate group-hover:text-brand-400 transition-colors flex items-center flex-wrap gap-1.5">
                      <span>{session.job_role || 'Interview Session'}</span>
                      {session.experience_level && (
                        <span className="text-xs font-normal text-slate-500">
                          ({session.experience_level})
                        </span>
                      )}
                      {session.interview_type === 'topic' ? (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium">
                          {session.focus_topic || 'Topic'}
                        </span>
                      ) : session.interview_type === 'role' ? (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 font-medium">
                          Role-Based
                        </span>
                      ) : (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/20 font-medium">
                          Resume-Based
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {formatDate(session.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3 ml-4 flex-shrink-0">
                    <StatusBadge status={session.status} />
                    <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-brand-400 transition-colors" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Quick Launch Banner */}
      <div className="mt-6">
        <Link
          to="/interview/setup"
          className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all group"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Start New Interview Session</h3>
              <p className="text-xs text-slate-500">
                Launch a personalized 7-stage mock session tailored to your uploaded resume
              </p>
            </div>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-600 group-hover:text-brand-400 transition-colors" />
        </Link>
      </div>
    </div>
  );
};
