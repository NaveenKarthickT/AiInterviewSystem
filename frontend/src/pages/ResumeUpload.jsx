import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { resumeApi } from '../api/resume';
import {
  UploadCloud,
  FileText,
  Trash2,
  PlayCircle,
  CheckCircle2,
  AlertCircle,
  Layers,
  Code2,
  Database,
  Cloud,
  Wrench,
  Sparkles,
  Briefcase,
  GraduationCap,
  ExternalLink,
  Loader2,
} from 'lucide-react';

export const ResumeUpload = () => {
  const [resumes, setResumes] = useState([]);
  const [selectedResume, setSelectedResume] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStage, setUploadStage] = useState('');
  const [loadingList, setLoadingList] = useState(true);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const fetchResumes = async () => {
    try {
      setLoadingList(true);
      const data = await resumeApi.listResumes();
      setResumes(data);
      if (data.length > 0 && !selectedResume) {
        // Load the most recent resume details
        loadResumeDetails(data[0].id);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch resumes.');
    } finally {
      setLoadingList(false);
    }
  };

  const loadResumeDetails = async (resumeId) => {
    try {
      const details = await resumeApi.getResume(resumeId);
      setSelectedResume(details);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const handleFileUpload = async (file) => {
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      setError('Please upload a valid PDF or DOCX resume.');
      return;
    }

    try {
      setError('');
      setUploading(true);
      setUploadStage('Extracting document contents via PyMuPDF / python-docx...');
      
      const newResume = await resumeApi.uploadResume(file);
      
      setUploadStage('Analyzing skills & structural evidence via AI Agent...');
      await fetchResumes();
      setSelectedResume(newResume);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Error uploading and processing resume.');
    } finally {
      setUploading(false);
      setUploadStage('');
    }
  };

  const handleDeleteResume = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this resume?')) return;
    try {
      await resumeApi.deleteResume(id);
      if (selectedResume?.id === id) {
        setSelectedResume(null);
      }
      await fetchResumes();
    } catch (err) {
      console.error(err);
      setError('Failed to delete resume.');
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Languages':
        return Code2;
      case 'Frameworks':
        return Layers;
      case 'Databases':
        return Database;
      case 'Cloud & DevOps':
        return Cloud;
      default:
        return Wrench;
    }
  };

  const getProficiencyColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'advanced':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'intermediate':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      default:
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center space-x-3">
            <span>Resume Intelligence & Skill Profiler</span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">
              Phase 2 Active
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Upload your resume to extract competencies, verify project evidence, and configure your adaptive mock interview.
          </p>
        </div>

        {selectedResume && (
          <button
            onClick={() => navigate(`/interview/setup?resumeId=${selectedResume.id}`)}
            className="inline-flex items-center space-x-2 bg-brand-600 hover:bg-brand-500 text-white font-medium px-5 py-2.5 rounded-xl shadow-lg shadow-brand-500/25 transition-all self-start sm:self-auto"
          >
            <PlayCircle className="w-5 h-5" />
            <span>Practice with This Resume</span>
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid: Upload & History on Left, Detailed Profile on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column (Upload + List) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Drag & Drop Zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              if (e.dataTransfer.files?.[0]) {
                handleFileUpload(e.dataTransfer.files[0]);
              }
            }}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-brand-500 bg-brand-500/5'
                : 'border-slate-800 hover:border-slate-700 bg-slate-900/60'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => handleFileUpload(e.target.files?.[0])}
              accept=".pdf,.docx,.doc"
              className="hidden"
            />
            <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center mx-auto mb-3">
              <UploadCloud className="w-6 h-6" />
            </div>
            <p className="text-sm font-semibold text-white">
              {uploading ? 'Processing Resume...' : 'Upload PDF or DOCX Resume'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Drag and drop or browse from your computer
            </p>
            <div className="mt-4 flex items-center justify-center space-x-2 text-[11px] text-slate-500 uppercase tracking-wider font-medium">
              <span>PDF</span>
              <span>•</span>
              <span>DOCX</span>
              <span>•</span>
              <span>Max 15MB</span>
            </div>

            {uploading && (
              <div className="mt-4 pt-4 border-t border-slate-800 text-xs text-brand-400 flex items-center justify-center space-x-2 animate-pulse">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{uploadStage || 'Analyzing...'}</span>
              </div>
            )}
          </div>

          {/* Uploaded Resumes List */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center justify-between">
              <span>Your Resumes</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {resumes.length}
              </span>
            </h3>

            {loadingList ? (
              <div className="py-8 text-center text-slate-500 text-sm flex items-center justify-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
                <span>Loading resumes...</span>
              </div>
            ) : resumes.length === 0 ? (
              <p className="py-6 text-center text-xs text-slate-500">
                No resumes uploaded yet. Upload one above to get started.
              </p>
            ) : (
              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {resumes.map((r) => {
                  const isSelected = selectedResume?.id === r.id;
                  return (
                    <div
                      key={r.id}
                      onClick={() => loadResumeDetails(r.id)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                        isSelected
                          ? 'bg-brand-500/10 border-brand-500/40'
                          : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center space-x-3 overflow-hidden">
                        <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0 text-slate-300">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div className="overflow-hidden">
                          <p className="text-sm font-medium text-white truncate">
                            {r.file_name}
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {r.skills_count} skills • {r.projects_count} projects
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={(e) => handleDeleteResume(r.id, e)}
                        className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors ml-2"
                        title="Delete resume"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Extracted Profile Details */}
        <div className="lg:col-span-8">
          {selectedResume ? (
            <div className="space-y-6">
              {/* Profile Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
                  <div>
                    <h2 className="text-2xl font-bold text-white">
                      {selectedResume.parsed_data?.full_name || 'Engineering Candidate'}
                    </h2>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-400">
                      {selectedResume.parsed_data?.email && (
                        <span>{selectedResume.parsed_data.email}</span>
                      )}
                      {selectedResume.parsed_data?.phone && (
                        <>
                          <span>•</span>
                          <span>{selectedResume.parsed_data.phone}</span>
                        </>
                      )}
                      {selectedResume.parsed_data?.github && (
                        <>
                          <span>•</span>
                          <span className="text-brand-400">{selectedResume.parsed_data.github}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <span className="inline-flex items-center space-x-1.5 text-xs font-semibold px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 self-start sm:self-auto">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Multi-Agent Parsed</span>
                  </span>
                </div>

                {/* Summary */}
                {selectedResume.summary && (
                  <div className="mt-5">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-brand-400" />
                      <span>Executive Technical Summary</span>
                    </h4>
                    <p className="text-slate-300 text-sm leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                      {selectedResume.summary}
                    </p>
                  </div>
                )}
              </div>

              {/* Categorized Skills Breakdown */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
                  <Code2 className="w-5 h-5 text-brand-400" />
                  <span>Profiled Competencies & Evidence ({selectedResume.extracted_skills?.length || 0})</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {(selectedResume.extracted_skills || []).map((skill, idx) => {
                    const CategoryIcon = getCategoryIcon(skill.category);
                    return (
                      <div
                        key={idx}
                        className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <div className="p-1 rounded bg-slate-800 text-slate-400">
                              <CategoryIcon className="w-3.5 h-3.5" />
                            </div>
                            <span className="font-semibold text-sm text-white">
                              {skill.name}
                            </span>
                          </div>
                          <span
                            className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${getProficiencyColor(
                              skill.proficiency
                            )}`}
                          >
                            {skill.proficiency}
                          </span>
                        </div>
                        {skill.evidence_summary && (
                          <p className="text-xs text-slate-400 mt-2.5 leading-snug">
                            {skill.evidence_summary}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Projects Extracted */}
              {selectedResume.parsed_data?.projects?.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
                    <Briefcase className="w-5 h-5 text-purple-400" />
                    <span>Technical Projects</span>
                  </h3>

                  <div className="space-y-4">
                    {selectedResume.parsed_data.projects.map((proj, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-slate-950/70 border border-slate-800"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                          <h4 className="text-base font-bold text-white">{proj.title}</h4>
                          {proj.role && (
                            <span className="text-xs text-slate-400 font-medium">
                              Role: {proj.role}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-300 leading-relaxed mb-3">
                          {proj.description}
                        </p>
                        {proj.metrics_or_impact && (
                          <div className="mb-3 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg inline-block">
                            Impact: {proj.metrics_or_impact}
                          </div>
                        )}
                        {proj.technologies?.length > 0 && (
                          <div className="flex flex-wrap gap-1.5">
                            {proj.technologies.map((t, i) => (
                              <span
                                key={i}
                                className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60"
                              >
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Education */}
              {selectedResume.parsed_data?.education?.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
                    <GraduationCap className="w-5 h-5 text-blue-400" />
                    <span>Education Background</span>
                  </h3>
                  <div className="space-y-3">
                    {selectedResume.parsed_data.education.map((edu, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between"
                      >
                        <div>
                          <p className="text-sm font-semibold text-white">{edu.degree}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{edu.institution}</p>
                        </div>
                        {edu.year && (
                          <span className="text-xs text-slate-400 font-medium bg-slate-800 px-2.5 py-1 rounded-md">
                            {edu.year}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
              <FileText className="w-12 h-12 mx-auto text-slate-600 mb-4" />
              <h3 className="text-base font-semibold text-slate-300">No Resume Selected</h3>
              <p className="text-xs text-slate-500 mt-1">
                Upload or select a resume on the left to inspect extracted skills and project evidence.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
