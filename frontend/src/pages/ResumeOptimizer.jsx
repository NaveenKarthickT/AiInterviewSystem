import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom';
import { optimizationApi } from '../api/optimization';
import { interviewApi } from '../api/interview';
import { DiffViewer } from '../components/DiffViewer';
import {
  Sparkles,
  FileText,
  Download,
  CheckCircle2,
  AlertCircle,
  Briefcase,
  TrendingUp,
  Award,
  Layers,
  ArrowRight,
  Filter,
  Check,
  Edit,
  Loader2,
  ExternalLink,
} from 'lucide-react';

export const ResumeOptimizer = () => {
  const { sessionId: paramSessionId } = useParams();
  const [searchParams] = useSearchParams();
  const querySessionId = searchParams.get('sessionId');
  const activeSessionId = paramSessionId || querySessionId;

  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(activeSessionId || '');
  const [optimization, setOptimization] = useState(null);
  const [items, setItems] = useState([]);
  const [filterAction, setFilterAction] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [compiling, setCompiling] = useState(false);
  const [downloadingFormat, setDownloadingFormat] = useState(null);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const navigate = useNavigate();

  // Load candidate interview sessions
  useEffect(() => {
    const loadSessions = async () => {
      try {
        const data = await interviewApi.listSessions();
        setSessions(data);
        if (!selectedSessionId && data.length > 0) {
          setSelectedSessionId(data[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadSessions();
  }, [selectedSessionId]);

  // Load or generate optimization analysis for selected session
  useEffect(() => {
    if (!selectedSessionId) {
      setLoading(false);
      return;
    }

    const loadOptimization = async () => {
      try {
        setLoading(true);
        setError('');
        const data = await optimizationApi.getOptimization(selectedSessionId);
        setOptimization(data);
        setItems(data.item_recommendations || []);
      } catch (err) {
        console.error(err);
        setError('Failed to generate resume optimization.');
      } finally {
        setLoading(false);
      }
    };

    loadOptimization();
  }, [selectedSessionId]);

  const handleToggleApproval = (itemId) => {
    setItems((prev) =>
      prev.map((i) => (i.id === itemId ? { ...i, approved: !i.approved } : i))
    );
  };

  const handleApproveAll = () => {
    setItems((prev) => prev.map((i) => ({ ...i, approved: true })));
  };

  const handleCompileResume = async () => {
    if (!optimization) return;

    try {
      setCompiling(true);
      setError('');
      setSuccessMsg('');

      const updated = await optimizationApi.approveAndCompile(
        optimization.id,
        items
      );
      setOptimization(updated);
      setSuccessMsg('ATS Resume successfully compiled and exported in PDF & DOCX formats!');
    } catch (err) {
      console.error(err);
      setError('Failed to compile ATS resume.');
    } finally {
      setCompiling(false);
    }
  };

  const handleDownloadFile = async (format) => {
    if (!optimization) return;
    try {
      setDownloadingFormat(format);
      setError('');
      setSuccessMsg('');
      await optimizationApi.downloadExportedFile(optimization.id, format);
      setSuccessMsg(`ATS Resume (${format.toUpperCase()}) downloaded successfully!`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || `Failed to download ${format.toUpperCase()} resume.`);
    } finally {
      setDownloadingFormat(null);
    }
  };

  const filteredItems = items.filter((i) => {
    if (filterAction === 'ALL') return true;
    return i.recommended_action === filterAction;
  });

  const counts = {
    KEEP: items.filter((i) => i.recommended_action === 'KEEP').length,
    MODIFY: items.filter((i) => i.recommended_action === 'MODIFY').length,
    VERIFY: items.filter((i) => i.recommended_action === 'VERIFY').length,
    REMOVE: items.filter((i) => i.recommended_action === 'REMOVE').length,
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
          <p className="text-slate-400 text-sm">Cross-referencing interview transcripts with resume claims...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Top Header */}
      <div className="bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 border border-slate-800 rounded-3xl p-8 mb-8 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Evidence-Grounded Resume Recommender</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Intelligent Resume Optimizer & ATS Exporter
            </h1>
            <p className="text-slate-300 text-sm mt-1">
              Transforms claims into verified STAR bullets based on your actual performance in{' '}
              <strong className="text-white">{optimization?.target_role}</strong> recruitment rounds.
            </p>
          </div>

          {/* Session Switcher */}
          {sessions.length > 1 && (
            <div className="flex items-center space-x-2 bg-slate-950/70 p-2 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 pl-2">Session:</span>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                className="bg-slate-900 text-slate-200 text-xs font-semibold py-1.5 px-3 rounded-lg border border-slate-700 outline-none"
              >
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.job_role} ({s.current_turn_count} turns)
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-start space-x-3 text-emerald-400 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Section 1: AI Job-Role Recommendations */}
      {optimization?.job_role_recommendations?.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
          <h2 className="text-base font-bold text-white mb-1 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Top Matched Job Roles Based on Verified Competence</span>
          </h2>
          <p className="text-xs text-slate-400 mb-5">
            Cross-referenced against engineering hiring benchmarks and your technical scores.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {optimization.job_role_recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <h3 className="text-sm font-bold text-white">{rec.role_title}</h3>
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                      {rec.match_percentage}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed mb-3">
                    {rec.justification}
                  </p>
                  
                  {rec.key_strengths?.length > 0 && (
                    <div className="mb-3">
                      <span className="text-[10px] font-bold uppercase text-slate-500 block mb-1">
                        Verified Strengths:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {rec.key_strengths.map((s, i) => (
                          <span
                            key={i}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {rec.recommended_upskill?.length > 0 && (
                  <div className="pt-2.5 border-t border-slate-800/80 text-[11px] text-amber-400">
                    <strong className="text-slate-400 font-semibold">Upskill to 95%:</strong>{' '}
                    {rec.recommended_upskill.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 2: Action Breakdown & Approval Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <FileText className="w-5 h-5 text-brand-400" />
              <span>Resume Items Optimization Diff ({items.length})</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Review and approve proposed changes. We never fabricate metrics or invent technologies.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleApproveAll}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              <Check className="w-4 h-4 text-emerald-400" />
              <span>Approve All ({items.length})</span>
            </button>

            <button
              type="button"
              onClick={handleCompileResume}
              disabled={compiling || items.length === 0}
              className="inline-flex items-center space-x-2 px-5 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white shadow-md shadow-brand-500/25 transition-all"
            >
              {compiling ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Compiling ATS Resume...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Compile & Export ATS Resume</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Action Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 mt-5">
          <span className="text-xs text-slate-500 mr-2 flex items-center space-x-1">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter:</span>
          </span>

          {[
            { id: 'ALL', label: `All Items (${items.length})` },
            { id: 'MODIFY', label: `Modify to STAR (${counts.MODIFY})` },
            { id: 'KEEP', label: `Keep (${counts.KEEP})` },
            { id: 'VERIFY', label: `Verify Tier (${counts.VERIFY})` },
            { id: 'REMOVE', label: `Remove (${counts.REMOVE})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterAction(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filterAction === tab.id
                  ? 'bg-brand-600/20 text-brand-400 border border-brand-500/40'
                  : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Export Downloads Card (if approved & compiled) */}
      {optimization?.status === 'approved' && (
        <div className="bg-gradient-to-r from-emerald-950/30 via-slate-900 to-emerald-950/30 border border-emerald-500/30 rounded-2xl p-6 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">ATS-Compliant Resume Ready for Download</h3>
              <p className="text-xs text-slate-400">
                Single-column ATS standard formatted with interview-grounded STAR accomplishments.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={() => handleDownloadFile('docx')}
              disabled={downloadingFormat !== null}
              className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 font-semibold px-4 py-2 rounded-xl border border-slate-700 text-xs transition-colors cursor-pointer"
            >
              {downloadingFormat === 'docx' ? (
                <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5 text-blue-400" />
              )}
              <span>Download DOCX</span>
            </button>
            <button
              type="button"
              onClick={() => handleDownloadFile('pdf')}
              disabled={downloadingFormat !== null}
              className="inline-flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold px-4 py-2 rounded-xl text-xs transition-colors shadow-sm shadow-emerald-500/25 cursor-pointer"
            >
              {downloadingFormat === 'pdf' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              <span>Download PDF</span>
            </button>
          </div>
        </div>
      )}

      {/* Section 3: Diff Cards Stream */}
      <div className="space-y-4">
        {filteredItems.map((item) => (
          <DiffViewer
            key={item.id}
            item={item}
            onToggleApproval={handleToggleApproval}
          />
        ))}

        {filteredItems.length === 0 && (
          <div className="p-8 text-center text-slate-500 text-xs bg-slate-900 border border-slate-800 rounded-2xl">
            No items match the selected filter.
          </div>
        )}
      </div>
    </div>
  );
};
