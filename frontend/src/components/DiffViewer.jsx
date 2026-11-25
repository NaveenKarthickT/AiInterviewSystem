import React from 'react';
import {
  CheckCircle2,
  Edit3,
  HelpCircle,
  Trash2,
  ArrowRight,
  ShieldCheck,
  Check,
  X,
} from 'lucide-react';

export const DiffViewer = ({ item, onToggleApproval, onTextChange }) => {
  const getActionBadge = (action) => {
    switch (action) {
      case 'KEEP':
        return {
          label: 'KEEP AS CORNERSTONE',
          color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
          icon: CheckCircle2,
        };
      case 'MODIFY':
        return {
          label: 'MODIFY TO STAR / IMPACT',
          color: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
          icon: Edit3,
        };
      case 'VERIFY':
        return {
          label: 'VERIFY PROFICIENCY',
          color: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
          icon: HelpCircle,
        };
      case 'REMOVE':
        return {
          label: 'REMOVE (OUTDATED / CLICHÉ)',
          color: 'bg-red-500/15 text-red-400 border-red-500/30',
          icon: Trash2,
        };
      default:
        return {
          label: action,
          color: 'bg-slate-800 text-slate-300 border-slate-700',
          icon: CheckCircle2,
        };
    }
  };

  const badge = getActionBadge(item.recommended_action);
  const Icon = badge.icon;

  return (
    <div
      className={`p-5 rounded-2xl border transition-all ${
        item.approved
          ? 'bg-slate-900 border-slate-800'
          : 'bg-slate-950/60 border-slate-850 opacity-60'
      }`}
    >
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2.5">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            {item.section}
          </span>
          <span className="text-slate-600">•</span>
          <span
            className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border flex items-center space-x-1.5 ${badge.color}`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{badge.label}</span>
          </span>
        </div>

        {/* Candidate Approval Toggle */}
        <button
          type="button"
          onClick={() => onToggleApproval(item.id)}
          className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            item.approved
              ? 'bg-brand-600/20 text-brand-300 border border-brand-500/40 hover:bg-brand-600/30'
              : 'bg-slate-800 text-slate-400 border border-slate-700 hover:text-white'
          }`}
        >
          {item.approved ? (
            <>
              <Check className="w-3.5 h-3.5 text-brand-400" />
              <span>Approved by Candidate</span>
            </>
          ) : (
            <>
              <X className="w-3.5 h-3.5 text-slate-500" />
              <span>Rejected / Skipped</span>
            </>
          )}
        </button>
      </div>

      {/* Diff Content */}
      <div className="space-y-3 text-xs">
        {/* Original Text */}
        <div>
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
            Original Resume Bullet / Claim:
          </span>
          <p className="text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800/80 font-mono text-[12px]">
            {item.original_text}
          </p>
        </div>

        {/* Suggested Replacement (if MODIFY) */}
        {item.recommended_action === 'MODIFY' && item.suggested_text && (
          <div>
            <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider block mb-1">
              Optimized STAR / XYZ Recommendation (Grounded in Interview Evidence):
            </span>
            <div className="p-3 rounded-xl bg-indigo-950/25 border border-indigo-500/30 text-indigo-200 font-medium text-[12px] leading-relaxed">
              {item.suggested_text}
            </div>
          </div>
        )}

        {/* Recommendation Reason */}
        <div className="pt-2 text-slate-400 flex items-start space-x-2 text-[11px] bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/40">
          <ShieldCheck className="w-3.5 h-3.5 text-brand-400 flex-shrink-0 mt-0.5" />
          <span>
            <strong className="text-slate-300">Why this recommendation:</strong> {item.reason}
          </span>
        </div>
      </div>
    </div>
  );
};
