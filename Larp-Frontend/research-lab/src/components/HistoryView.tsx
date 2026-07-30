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
    <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#F7F9FB]">
      <div className="max-w-[840px] mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-[#C6C6CD] pb-4">
          <div>
            <h2 className="text-[24px] font-bold text-[#0F172A]">Research History</h2>
            <p className="text-[14px] text-[#45464D] mt-0.5">
              Review and resume past academic research protocols and synthesis threads.
            </p>
          </div>
          <span className="text-[12px] font-bold bg-[#E0E3E5] px-3 py-1 rounded-full text-[#0F172A]">
            {filtered.length} Threads
          </span>
        </div>

        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg border border-[#C6C6CD] p-8">
              <span className="material-symbols-outlined text-[36px] text-[#76777D] mb-2">
                history
              </span>
              <p className="text-[#45464D] font-medium text-[15px]">No research history matches your query.</p>
            </div>
          ) : (
            filtered.map((p) => (
              <div
                key={p.id}
                onClick={() => onSelectProject(p)}
                className="bg-white border border-[#C6C6CD] rounded-lg p-5 hover:border-[#0F172A] transition-all cursor-pointer group flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-2xs"
              >
                <div className="space-y-1 min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#003EA8] bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                      {p.category}
                    </span>
                    <span className="text-[12px] text-[#76777D] font-mono">• {p.dateLabel}</span>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#45464D]">
                      ({p.mode === 'deep' ? 'Deep Dive' : 'Quick Scan'})
                    </span>
                  </div>
                  <h3 className="font-bold text-[17px] text-[#0F172A] group-hover:text-[#2563EB] transition-colors truncate">
                    {p.title}
                  </h3>
                  <p className="text-[14px] text-[#45464D] line-clamp-1 italic">
                    "{p.query}"
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleStar(p.id);
                    }}
                    className={`p-1.5 rounded-full hover:bg-[#E0E3E5] transition-colors ${
                      p.isStarred ? 'text-amber-500' : 'text-[#76777D]'
                    }`}
                    title={p.isStarred ? 'Unstar' : 'Star'}
                  >
                    <span className={`material-symbols-outlined ${p.isStarred ? 'fill-1' : ''}`}>
                      star
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteProject(p.id);
                    }}
                    className="p-1.5 rounded-full text-[#76777D] hover:text-red-600 hover:bg-[#E0E3E5] transition-colors"
                    title="Delete Thread"
                  >
                    <span className="material-symbols-outlined">delete</span>
                  </button>

                  <button
                    type="button"
                    className="px-4 py-2 bg-[#0F172A] text-white font-bold text-[12px] uppercase tracking-wider rounded-md hover:bg-slate-800 transition-colors flex items-center gap-1"
                  >
                    Resume
                    <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
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
