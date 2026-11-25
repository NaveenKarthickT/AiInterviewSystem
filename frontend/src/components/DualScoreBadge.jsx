import React, { useState } from 'react';
import {
  Award,
  Layers,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Sparkles,
} from 'lucide-react';

export const DualScoreBadge = ({ evaluation }) => {
  const [expanded, setExpanded] = useState(false);

  if (!evaluation) return null;

  const { knowledge, communication } = evaluation;

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (score >= 60) return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
    return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
  };

  return (
    <div className="mt-3 bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden transition-all">
      {/* Summary Header */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="p-3.5 flex flex-wrap items-center justify-between gap-3 cursor-pointer hover:bg-slate-900/50 transition-colors"
      >
        <div className="flex items-center space-x-4">
          {/* Knowledge Score */}
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/15 text-indigo-400">
              <Award className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Technical Knowledge
              </span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${getScoreColor(knowledge.knowledge_score)}`}>
                {knowledge.knowledge_score} / 100
              </span>
            </div>
          </div>

          <div className="h-6 w-px bg-slate-800" />

          {/* Communication Score */}
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-amber-500/15 text-amber-400">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Communication Delivery
              </span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${getScoreColor(communication.comm_score)}`}>
                {communication.comm_score} / 100
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-medium text-slate-400">
          <span>{expanded ? 'Hide Evaluation Details' : 'View Independent Feedback'}</span>
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </div>

      {/* Expandable Breakdown Drawer */}
      {expanded && (
        <div className="p-4 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Technical Evaluation Column */}
          <div className="bg-slate-900/60 rounded-xl p-3.5 border border-indigo-500/20">
            <h4 className="font-bold text-indigo-300 flex items-center space-x-1.5 mb-2.5">
              <Award className="w-4 h-4" />
              <span>Technical Knowledge Evaluation</span>
            </h4>

            <p className="text-slate-300 leading-relaxed mb-3">
              {knowledge.knowledge_feedback}
            </p>

            <div className="space-y-1.5 mb-3 text-[11px] text-slate-400">
              <div className="flex justify-between">
                <span>Correctness:</span>
                <span className="text-white font-semibold">{knowledge.technical_correctness} / 30</span>
              </div>
              <div className="flex justify-between">
                <span>Conceptual Depth:</span>
                <span className="text-white font-semibold">{knowledge.conceptual_depth} / 25</span>
              </div>
              <div className="flex justify-between">
                <span>Practical Trade-offs:</span>
                <span className="text-white font-semibold">{knowledge.practical_application} / 25</span>
              </div>
              <div className="flex justify-between">
                <span>Problem Solving:</span>
                <span className="text-white font-semibold">{knowledge.problem_solving} / 20</span>
              </div>
            </div>

            {knowledge.knowledge_strengths?.length > 0 && (
              <div className="mt-2 text-emerald-400">
                <span className="font-semibold block mb-1">Demonstrated Strengths:</span>
                <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                  {knowledge.knowledge_strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {knowledge.missing_concepts?.length > 0 && (
              <div className="mt-2.5 text-amber-400">
                <span className="font-semibold block mb-1">Key Concepts to Review:</span>
                <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                  {knowledge.missing_concepts.map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Communication Evaluation Column */}
          <div className="bg-slate-900/60 rounded-xl p-3.5 border border-amber-500/20">
            <h4 className="font-bold text-amber-300 flex items-center space-x-1.5 mb-2.5">
              <Layers className="w-4 h-4" />
              <span>Communication & Delivery Evaluation</span>
            </h4>

            <p className="text-slate-300 leading-relaxed mb-3">
              {communication.structure_feedback}
            </p>

            <div className="space-y-1.5 mb-3 text-[11px] text-slate-400">
              <div className="flex justify-between">
                <span>Clarity & Organization:</span>
                <span className="text-white font-semibold">{communication.clarity_score} / 30</span>
              </div>
              <div className="flex justify-between">
                <span>Conciseness:</span>
                <span className="text-white font-semibold">{communication.conciseness_score} / 25</span>
              </div>
              <div className="flex justify-between">
                <span>Professional Vocabulary:</span>
                <span className="text-white font-semibold">{communication.professional_vocabulary} / 25</span>
              </div>
              <div className="flex justify-between">
                <span>Grammar & Cohesion:</span>
                <span className="text-white font-semibold">{communication.grammar_and_coherence} / 20</span>
              </div>
            </div>

            {communication.comm_strengths?.length > 0 && (
              <div className="mt-2 text-emerald-400">
                <span className="font-semibold block mb-1">Delivery Strengths:</span>
                <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                  {communication.comm_strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {communication.comm_weaknesses?.length > 0 && (
              <div className="mt-2.5 text-amber-400">
                <span className="font-semibold block mb-1">Delivery Polish:</span>
                <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                  {communication.comm_weaknesses.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
