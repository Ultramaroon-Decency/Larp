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
    <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#18181B] text-[#F4F4F5]">
      <div className="max-w-[760px] mx-auto space-y-6">
        <div className="flex items-center justify-between pb-4">
          <div>
            <h2 className="text-[24px] font-bold tracking-tight">Research History</h2>
          </div>
          <span className="text-[11px] font-bold bg-[#27272A] px-3 py-1 rounded-full text-[#A1A1AA]">
            {filtered.length} Sessions
          </span>
        </div>

        <div className="space-y-1">
          {filtered.length === 0 ? (
            <div className="text-center py-12">
              <span className="material-symbols-outlined text-[32px] text-[#3F3F46] mb-2">
                history
              </span>
              <p className="text-[#A1A1AA] text-[14px]">No research history matches your query.</p>
            </div>
          ) : (
            filtered.map((p) => (
              <div
                key={p.id}
                onClick={() => onSelectProject(p)}
                className="group flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl hover:bg-[#27272A] transition-colors cursor-pointer"
              >
                <div className="space-y-1 min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[12px] text-[#A1A1AA] font-mono">{p.dateLabel}</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#76777D] bg-[#27272A] px-1.5 py-0.5 rounded">
                      {p.mode === 'deep' ? 'Deep Dive' : 'Quick Scan'}
                    </span>
                  </div>
                  <h3 className="font-medium text-[15px] text-[#F4F4F5] truncate">
                    {p.title}
                  </h3>
                  <p className="text-[13px] text-[#A1A1AA] line-clamp-1">
                    {p.query}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0 md:opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleStar(p.id);
                    }}
                    className={`p-2 rounded-lg hover:bg-[#3F3F46] transition-colors ${
                      p.isStarred ? 'text-[#10B981]' : 'text-[#76777D]'
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
                    className="p-2 rounded-lg text-[#76777D] hover:text-red-400 hover:bg-[#3F3F46] transition-colors"
                    title="Delete Thread"
                  >
                    <span className="material-symbols-outlined text-[18px]">delete</span>
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
