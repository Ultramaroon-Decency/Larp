// src/components/HistoryView.tsx
import React from 'react';
import { ResearchProject } from '../types';

interface HistoryViewProps {
  projects: ResearchProject[];
  onSelectProject: (project: ResearchProject) => void;
  onToggleStar: (id: string) => void;
  onDeleteProject: (id: string) => void;
  searchQuery: string;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  projects,
  onSelectProject,
  onToggleStar,
  onDeleteProject,
  searchQuery
}) => {
  const filtered = projects.filter(
    (p) =>
      !searchQuery ||
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.query.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-8 bg-[#090D16] text-[#E5E7EB]">
      <div className="max-w-[760px] mx-auto space-y-6">
        {/* Header Section */}
        <div className="flex items-center justify-between border-b border-[#1B2536] pb-4">
          <div>
            <h2 className="text-[20px] font-bold text-white">Research History</h2>
            <p className="text-[12px] text-zinc-400 mt-0.5">
              Review and resume past academic research protocols and synthesis threads.
            </p>
          </div>
          <span className="text-[10px] font-bold bg-[#131E31] px-2.5 py-1 rounded-full text-primary border border-primary/20">
            {filtered.length} Threads
          </span>
        </div>

        {/* List of past threads */}
        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="text-center py-12 bg-[#0D1525] rounded-xl border border-[#1B2536] p-8 text-zinc-500">
              <span className="material-symbols-outlined text-[32px] text-zinc-600 mb-2 block">
                history
              </span>
              <p className="text-zinc-400 font-medium text-[13px]">No research history matches your query.</p>
            </div>
          ) : (
            filtered.map((p) => (
              <div
                key={p.id}
                onClick={() => onSelectProject(p)}
                className="bg-[#0D1525] border border-[#1B2536] rounded-xl p-4.5 hover:border-primary/50 transition-all cursor-pointer group flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm"
              >
                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/25">
                      {p.category}
                    </span>
                    <span className="text-[11px] text-zinc-500 font-mono">• {p.dateLabel}</span>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-zinc-400">
                      ({p.mode === 'deep' ? 'Deep Dive' : 'Quick Scan'})
                    </span>
                  </div>
                  <h3 className="font-bold text-[15px] text-white group-hover:text-primary transition-colors truncate">
                    {p.title}
                  </h3>
                  <p className="text-[13px] text-zinc-400 line-clamp-1 italic leading-relaxed">
                    &ldquo;{p.query}&rdquo;
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2.5 shrink-0 self-end md:self-center">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleStar(p.id);
                    }}
                    className={`p-1.5 rounded-lg hover:bg-zinc-800 transition-colors outline-none cursor-pointer ${
                      p.isStarred ? 'text-amber-500' : 'text-zinc-500 hover:text-white'
                    }`}
                    title={p.isStarred ? 'Unstar' : 'Star'}
                  >
                    <span className={`material-symbols-outlined text-[18px] ${p.isStarred ? 'fill-1' : ''}`}>
                      star
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteProject(p.id);
                    }}
                    className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-zinc-800 transition-colors outline-none cursor-pointer"
                    title="Delete Thread"
                  >
                    <span className="material-symbols-outlined text-[18px]">delete</span>
                  </button>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectProject(p);
                    }}
                    className="px-3 py-1.5 bg-primary text-white font-bold text-[11px] uppercase tracking-wider rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-1 outline-none cursor-pointer"
                  >
                    Resume
                    <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
