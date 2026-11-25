import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { resumeApi } from '../api/resume';
import { interviewApi } from '../api/interview';
import {
  PlayCircle,
  Briefcase,
  Layers,
  Mic,
  MessageSquare,
  Sparkles,
  FileText,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  ShieldCheck,
  Cpu,
  Server,
  Layout,
  Terminal,
  Brain,
  Sliders,
  Loader2,
  BookOpen,
  Target,
  Database,
  Network,
  Code,
  Shuffle,
  Flame,
} from 'lucide-react';

export const InterviewSetup = () => {
  const [searchParams] = useSearchParams();
  const preselectedResumeId = searchParams.get('resumeId');

  // Mode Selection: 'resume' | 'role' | 'topic'
  const [interviewType, setInterviewType] = useState('resume');

  // Resume Selection
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState(preselectedResumeId || '');

  // Role Selection
  const [jobRole, setJobRole] = useState('Full Stack Engineer');
  const [customRole, setCustomRole] = useState('');
  const [isCustomRole, setIsCustomRole] = useState(false);

  // Topic Selection
  const [focusTopic, setFocusTopic] = useState('System Design & Distributed Systems');
  const [customTopic, setCustomTopic] = useState('');
  const [isCustomTopic, setIsCustomTopic] = useState(false);

  // Seniority & Interaction Mode
  const [experienceLevel, setExperienceLevel] = useState('junior');
  const [interactionMode, setInteractionMode] = useState('text');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const interviewModes = [
    {
      id: 'resume',
      title: 'Resume-Based',
      icon: FileText,
      badge: 'Project & Experience Deep Dive',
      desc: 'Verify claims, frameworks, architecture, and projects from your uploaded resume.',
    },
    {
      id: 'role',
      title: 'Role-Based',
      icon: Target,
      badge: 'Competency & Standard Benchmark',
      desc: 'Rigorously test the essential architectural, systems, and day-to-day duties of a specific engineering job role.',
    },
    {
      id: 'topic',
      title: 'Topic-Based',
      icon: BookOpen,
      badge: 'Specialized Domain Mastery',
      desc: 'Concentrate on an engineering subject (e.g. System Design, OS Concurrency, Database Internals) with deep questions.',
    },
  ];

  const rolePresets = [
    { id: 'fullstack', title: 'Full Stack Engineer', icon: Layout, desc: 'Web architecture, API integration, front-to-back engineering' },
    { id: 'backend', title: 'Backend Systems Engineer', icon: Server, desc: 'Concurrency, database optimization, microservices & caching' },
    { id: 'frontend', title: 'Frontend Specialist', icon: Layout, desc: 'Component lifecycle, CSS/Tailwind, performance & state trees' },
    { id: 'devops', title: 'DevOps & Cloud Engineer', icon: Terminal, desc: 'CI/CD, Docker, Kubernetes, Linux internals & cloud security' },
    { id: 'ml', title: 'AI & Machine Learning Engineer', icon: Brain, desc: 'Model architectures, vector embeddings, training & inference' },
    { id: 'systems', title: 'Systems & Embedded Engineer', icon: Cpu, desc: 'Memory management, low-level concurrency, OS internals' },
  ];

  const topicPresets = [
    {
      id: 'system_design',
      title: 'System Design & Distributed Systems',
      icon: Network,
      desc: 'CAP theorem, microservices, consensus, sharding, caching tiers & rate limiters',
    },
    {
      id: 'dsa',
      title: 'Data Structures & Algorithms',
      icon: Code,
      desc: 'Trees, graphs, dynamic programming, sliding window, and amortized complexity',
    },
    {
      id: 'databases',
      title: 'Database Internals & SQL Optimization',
      icon: Database,
      desc: 'B+ Trees, WAL, ACID transaction isolation, indexes, vacuuming & query planners',
    },
    {
      id: 'concurrency',
      title: 'Operating Systems & Concurrency',
      icon: Cpu,
      desc: 'Threads, mutexes, condition variables, deadlocks, virtual memory & epoll / async I/O',
    },
    {
      id: 'networks',
      title: 'Computer Networks & Web Protocols',
      icon: Network,
      desc: 'TCP handshake, flow control, TLS 1.3, HTTP/2 & HTTP/3 multiplexing, DNS & CDN',
    },
    {
      id: 'frontend_arch',
      title: 'React & Frontend Architecture',
      icon: Layout,
      desc: 'Fiber reconciler, synthetic events, memory leaks, SSR/hydration & bundle profiling',
    },
    {
      id: 'cloud_k8s',
      title: 'Cloud Architecture & Kubernetes',
      icon: Terminal,
      desc: 'Pod lifecycle, ingress controllers, service mesh, zero-downtime rolling deploys & IAM',
    },
    {
      id: 'ai_engineering',
      title: 'LLM Systems & Machine Learning Engineering',
      icon: Brain,
      desc: 'RAG pipelines, vector index quantization, context window limits, prompt caching & inference',
    },
  ];

  const stagesList = [
    { id: 'intro', num: '1', title: 'Introduction', desc: 'Background & role motivation' },
    { id: 'skill_verification', num: '2', title: 'Skill Verification', desc: 'Direct probing of claimed technologies or core concepts' },
    { id: 'technical', num: '3', title: 'Technical Questions', desc: 'Core fundamentals & framework mechanics' },
    { id: 'problem_solving', num: '4', title: 'Problem Solving & Coding', desc: 'Algorithmic reasoning & architecture scenarios' },
    { id: 'project_discussion', num: '5', title: 'Project Deep Dive', desc: 'Personal contributions, blockers & metrics' },
    { id: 'experience_discussion', num: '6', title: 'Engineering Practices', desc: 'CI/CD, code review & production debugging' },
    { id: 'behavioral_hr', num: '7', title: 'Behavioral & Leadership', desc: 'Constructive conflict, prioritization & culture' },
  ];

  useEffect(() => {
    const loadResumes = async () => {
      try {
        setLoading(true);
        const data = await resumeApi.listResumes();
        setResumes(data);
        if (!selectedResumeId && data.length > 0) {
          setSelectedResumeId(data[0].id);
        }
      } catch (err) {
        console.error(err);
        setError('Failed to load candidate resumes.');
      } finally {
        setLoading(false);
      }
    };
    loadResumes();
  }, [preselectedResumeId]);

  const handleLaunchInterview = async () => {
    if (interviewType === 'resume' && !selectedResumeId) {
      setError('Please select or upload a resume for a Resume-Based interview.');
      return;
    }

    const effectiveRole = isCustomRole ? customRole.trim() : jobRole;
    if (!effectiveRole) {
      setError('Please provide a target job role.');
      return;
    }

    const effectiveTopic = isCustomTopic ? customTopic.trim() : focusTopic;
    if (interviewType === 'topic' && !effectiveTopic) {
      setError('Please select or specify a focus topic.');
      return;
    }

    try {
      setError('');
      setSubmitting(true);

      const session = await interviewApi.createSession({
        resume_id: selectedResumeId || null,
        interview_type: interviewType,
        focus_topic: interviewType === 'topic' ? effectiveTopic : null,
        job_role: effectiveRole,
        experience_level: experienceLevel,
        interaction_mode: interactionMode,
      });

      // Navigate to live interview with session
      navigate(`/interview/live/${session.id}`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to initialize adaptive interview session.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold">
            <Sliders className="w-3.5 h-3.5" />
            <span>Multi-Stage Recruitment Engine</span>
          </div>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold">
            <Shuffle className="w-3.5 h-3.5" />
            <span>Zero-Repetition Question Engine</span>
          </div>
        </div>

        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Configure Your Adaptive Mock Interview
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Choose your interview format: Resume-Based, Role-Based, or Topic-Based.
          Questions are dynamically synthesized with diverse real-world scenario constraints and zero duplicate repeats.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-8">
        {/* Section 1: Interview Mode Switcher */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-base font-bold text-white uppercase tracking-wider text-xs mb-3 flex items-center space-x-2 text-slate-300">
            <Sparkles className="w-4 h-4 text-brand-400" />
            <span>1. Select Interview Mode</span>
          </h2>
          <p className="text-xs text-slate-400 mb-4">
            Select how the AI agents should orient the trajectory and question generation.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {interviewModes.map((mode) => {
              const Icon = mode.icon;
              const isSelected = interviewType === mode.id;
              return (
                <div
                  key={mode.id}
                  onClick={() => setInterviewType(mode.id)}
                  className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'bg-gradient-to-br from-brand-950/60 to-slate-900 border-brand-500 shadow-lg shadow-brand-500/15 ring-1 ring-brand-500'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div
                        className={`p-2.5 rounded-xl ${
                          isSelected ? 'bg-brand-500 text-white' : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                          isSelected
                            ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {mode.id}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-white mb-1">{mode.title}</h3>
                    <p className="text-xs text-brand-400 font-medium mb-2">{mode.badge}</p>
                    <p className="text-xs text-slate-400 leading-relaxed">{mode.desc}</p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-[11px] text-slate-400 font-medium">
                      {mode.id === 'resume'
                        ? 'Requires uploaded resume'
                        : mode.id === 'role'
                        ? 'Resume optional'
                        : 'Resume optional'}
                    </span>
                    <div
                      className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                        isSelected ? 'border-brand-500 bg-brand-500 text-white' : 'border-slate-600'
                      }`}
                    >
                      {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Section 2A: Topic Selection (Visible if Topic Mode) */}
        {interviewType === 'topic' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 transition-all animate-fadeIn">
            <h2 className="text-base font-bold text-white uppercase tracking-wider text-xs mb-4 flex items-center space-x-2 text-slate-300">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              <span>2. Choose Your Focus Topic</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-4">
              {topicPresets.map((preset) => {
                const Icon = preset.icon;
                const isSelected = !isCustomTopic && focusTopic === preset.title;
                return (
                  <div
                    key={preset.id}
                    onClick={() => {
                      setIsCustomTopic(false);
                      setFocusTopic(preset.title);
                    }}
                    className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                      isSelected
                        ? 'bg-emerald-500/15 border-emerald-500 shadow-md shadow-emerald-500/10'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center space-x-2.5 mb-2">
                        <div className="p-2 rounded-lg bg-slate-800 text-emerald-400 flex-shrink-0">
                          <Icon className="w-4 h-4" />
                        </div>
                        <h3 className="text-xs font-bold text-white leading-tight">{preset.title}</h3>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-snug">{preset.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Custom Topic Input */}
            <div className="mt-4 pt-4 border-t border-slate-800 flex flex-wrap items-center gap-3">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="customTopicToggle"
                  checked={isCustomTopic}
                  onChange={(e) => setIsCustomTopic(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-700 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="customTopicToggle" className="text-xs font-semibold text-slate-300 cursor-pointer">
                  Or specify a custom niche topic:
                </label>
              </div>
              {isCustomTopic && (
                <input
                  type="text"
                  placeholder="e.g. Distributed Consensus & Raft/Paxos"
                  value={customTopic}
                  onChange={(e) => setCustomTopic(e.target.value)}
                  className="flex-1 min-w-[240px] bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-xl px-3.5 py-2 text-sm text-slate-100 outline-none"
                />
              )}
            </div>
          </div>
        )}

        {/* Section 2B: Target Engineering Role */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-base font-bold text-white uppercase tracking-wider text-xs mb-4 flex items-center space-x-2 text-slate-300">
            <Briefcase className="w-4 h-4 text-purple-400" />
            <span>{interviewType === 'topic' ? '3. Target Role Context' : '2. Target Engineering Role'}</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 mb-4">
            {rolePresets.map((preset) => {
              const Icon = preset.icon;
              const isSelected = !isCustomRole && jobRole === preset.title;
              return (
                <div
                  key={preset.id}
                  onClick={() => {
                    setIsCustomRole(false);
                    setJobRole(preset.title);
                  }}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'bg-purple-500/15 border-purple-500 shadow-md shadow-purple-500/10'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="p-2 rounded-lg bg-slate-800 text-purple-400">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h3 className="text-sm font-bold text-white">{preset.title}</h3>
                  </div>
                  <p className="text-xs text-slate-400 leading-snug">{preset.desc}</p>
                </div>
              );
            })}
          </div>

          {/* Custom Role Input */}
          <div className="mt-4 pt-4 border-t border-slate-800 flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="customRoleToggle"
                checked={isCustomRole}
                onChange={(e) => setIsCustomRole(e.target.checked)}
                className="rounded bg-slate-950 border-slate-700 text-brand-600 focus:ring-brand-500"
              />
              <label htmlFor="customRoleToggle" className="text-xs font-semibold text-slate-300 cursor-pointer">
                Or specify a custom niche job role:
              </label>
            </div>
            {isCustomRole && (
              <input
                type="text"
                placeholder="e.g. Distributed Database Core Engineer"
                value={customRole}
                onChange={(e) => setCustomRole(e.target.value)}
                className="flex-1 min-w-[240px] bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-xl px-3.5 py-2 text-sm text-slate-100 outline-none"
              />
            )}
          </div>
        </div>

        {/* Section 3: Baseline Resume (Required for Resume-mode, Optional for others) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-white uppercase tracking-wider text-xs flex items-center space-x-2 text-slate-300">
              <FileText className="w-4 h-4 text-brand-400" />
              <span>
                {interviewType === 'resume'
                  ? '3. Select Candidate Resume (Required)'
                  : '4. Attach Candidate Resume (Optional)'}
              </span>
            </h2>
            {interviewType !== 'resume' && (
              <span className="text-[11px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
                Optional for {interviewType === 'topic' ? 'Topic-Based' : 'Role-Based'}
              </span>
            )}
          </div>

          {loading ? (
            <div className="py-4 text-slate-500 text-sm flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
              <span>Loading resumes...</span>
            </div>
          ) : resumes.length === 0 ? (
            <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 text-center">
              <p className="text-sm text-slate-400 mb-3">No resumes uploaded yet.</p>
              {interviewType === 'resume' ? (
                <button
                  onClick={() => navigate('/resumes')}
                  className="inline-flex items-center space-x-2 text-sm font-semibold bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-xl transition-all"
                >
                  <span>Upload a Resume</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <p className="text-xs text-emerald-400">
                  You can proceed without a resume in {interviewType === 'topic' ? 'Topic' : 'Role'} mode!
                </p>
              )}
            </div>
          ) : (
            <div>
              {interviewType !== 'resume' && (
                <div className="mb-3">
                  <button
                    type="button"
                    onClick={() => setSelectedResumeId('')}
                    className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                      !selectedResumeId
                        ? 'bg-brand-500/20 border-brand-500 text-brand-300 font-semibold'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Proceed without attaching a resume
                  </button>
                </div>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {resumes.map((r) => {
                  const isSelected = selectedResumeId === r.id;
                  return (
                    <div
                      key={r.id}
                      onClick={() => setSelectedResumeId(r.id)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all flex items-start space-x-3 ${
                        isSelected
                          ? 'bg-brand-500/15 border-brand-500 shadow-md shadow-brand-500/10'
                          : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="p-2 rounded-lg bg-slate-800 text-slate-300 flex-shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="overflow-hidden">
                        <p className="text-sm font-semibold text-white truncate">{r.file_name}</p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {r.skills_count} skills • {r.projects_count} projects
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Section 4: Seniority & Interaction Mode */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Seniority Tier */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-bold text-white uppercase tracking-wider text-xs mb-4 flex items-center space-x-2 text-slate-300">
              <Layers className="w-4 h-4 text-emerald-400" />
              <span>Target Seniority Tier</span>
            </h2>

            <div className="space-y-2.5">
              {[
                { id: 'entry_level', label: 'Entry Level / Campus Intern', desc: 'Fundamentals, basic problem-solving, coursework projects' },
                { id: 'junior', label: 'Junior Engineer (0-2 Years)', desc: 'Framework mechanics, testing, clean code, real projects' },
                { id: 'mid_level', label: 'Associate / Mid Engineer (2-4 Years)', desc: 'System design trade-offs, concurrency, production incidents' },
              ].map((tier) => (
                <div
                  key={tier.id}
                  onClick={() => setExperienceLevel(tier.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    experienceLevel === tier.id
                      ? 'bg-emerald-500/15 border-emerald-500 text-white'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <p className="text-sm font-semibold">{tier.label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{tier.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Interaction Mode */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-bold text-white uppercase tracking-wider text-xs mb-4 flex items-center space-x-2 text-slate-300">
              <Mic className="w-4 h-4 text-blue-400" />
              <span>Interaction Mode</span>
            </h2>

            <div className="space-y-2.5">
              {[
                { id: 'text', icon: MessageSquare, label: 'Text Interview', desc: 'Type answers at your own pace with real-time feedback' },
                { id: 'voice', icon: Mic, label: 'Voice-Assisted Interview', desc: 'Speak naturally via microphone with speech-to-text integration' },
              ].map((mode) => {
                const Icon = mode.icon;
                return (
                  <div
                    key={mode.id}
                    onClick={() => setInteractionMode(mode.id)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-start space-x-3 ${
                      interactionMode === mode.id
                        ? 'bg-blue-500/15 border-blue-500 text-white'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="p-2 rounded-lg bg-slate-800 text-blue-400 flex-shrink-0 mt-0.5">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold">{mode.label}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{mode.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Section 5: 7-Stage Workflow Preview */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-base font-bold text-white uppercase tracking-wider text-xs mb-4 flex items-center justify-between text-slate-300">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-brand-400" />
              <span>Realistic Recruitment Sequence (7 Stages)</span>
            </div>
            <span className="text-[11px] text-brand-400 font-semibold px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
              {interviewType === 'topic' ? 'Specialized Domain Agenda' : 'Context-Driven Sequence'}
            </span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {stagesList.map((st) => (
              <div
                key={st.id}
                className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center space-x-2 mb-1.5">
                    <span className="w-5 h-5 rounded-full bg-brand-600/30 text-brand-300 text-xs font-bold flex items-center justify-center">
                      {st.num}
                    </span>
                    <span className="text-xs font-bold text-white">{st.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-tight">{st.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Submit Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-6 bg-gradient-to-r from-slate-900 via-brand-950/40 to-slate-900 border border-slate-800 rounded-2xl">
          <div>
            <p className="text-sm font-bold text-white">Ready to begin your session?</p>
            <p className="text-xs text-slate-400">
              The AI Interview Planner Agent will formulate your custom agenda with zero repetition.
            </p>
          </div>

          <button
            onClick={handleLaunchInterview}
            disabled={submitting || (interviewType === 'resume' && !selectedResumeId)}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-medium px-8 py-3.5 rounded-xl shadow-lg shadow-brand-500/25 transition-all text-sm group"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating Agenda & Questions...</span>
              </>
            ) : (
              <>
                <PlayCircle className="w-5 h-5" />
                <span>Launch Adaptive Interview</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
