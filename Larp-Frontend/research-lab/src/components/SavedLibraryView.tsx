import React, { useState } from 'react';
import { Collection, ResearchProject } from '../types';

interface SavedLibraryViewProps {
  collections: Collection[];
  projects: ResearchProject[];
  onSelectProject: (project: ResearchProject) => void;
  onOpenBibliography: (project: ResearchProject) => void;
  searchQuery: string;
}

export const SavedLibraryView: React.FC<SavedLibraryViewProps> = ({
  collections,
  projects,
  onSelectProject,
  onOpenBibliography,
  searchQuery
}) => {
  const [filter, setFilter] = useState<'all' | 'recent' | 'starred' | 'shared'>('all');

  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      !searchQuery ||
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (filter === 'starred') return p.isStarred;
    if (filter === 'shared') return p.isShared;
    return true;
  });

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#18181B] text-[#F4F4F5]">
      <div className="max-w-[760px] mx-auto space-y-8">
        {/* Filters */}
        <div className="flex flex-wrap gap-4 items-center justify-between pb-2">
          <div className="flex gap-2">
            {(['all', 'recent', 'starred', 'shared'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg transition-colors text-[13px] font-medium capitalize ${
                  filter === f
                    ? 'bg-[#27272A] text-[#F4F4F5]'
                    : 'text-[#A1A1AA] hover:bg-[#27272A] hover:text-[#D4D4D8]'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Collections */}
        <section>
          <h3 className="text-[12px] font-bold tracking-wider text-[#76777D] uppercase mb-4 px-2">
            Collections
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {collections.map((col) => (
              <div
                key={col.id}
                onClick={() => {
                  const matched = projects.find((p) => col.projectIds.includes(p.id)) || projects[0];
                  if (matched) onOpenBibliography(matched);
                }}
                className="bg-[#18181B] border border-[#27272A] rounded-xl p-4 hover:border-[#3F3F46] hover:bg-[#27272A] cursor-pointer transition-colors group flex items-center gap-4"
              >
                <div className="w-10 h-10 rounded-lg bg-[#27272A] flex items-center justify-center text-[#10B981] group-hover:bg-[#3F3F46] transition-colors shrink-0">
                  <span className="material-symbols-outlined text-[20px]">
                    {col.icon}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-[14px] text-[#F4F4F5] truncate">
                    {col.title}
                  </h4>
                  <div className="flex items-center gap-3 text-[12px] text-[#A1A1AA] mt-0.5">
                    <span>{col.refsCount} refs</span>
                    <span>•</span>
                    <span>{col.updatedAgo}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Documents */}
        <section>
          <div className="flex justify-between items-center mb-4 px-2">
            <h3 className="text-[12px] font-bold tracking-wider text-[#76777D] uppercase">
              Documents & Drafts
            </h3>
            <span className="text-[12px] text-[#A1A1AA]">
              {filteredProjects.length} items
            </span>
          </div>

          <div className="flex flex-col gap-1">
            {filteredProjects.map((p) => {
              const isPdf = p.title.toLowerCase().endsWith('.pdf');
              const isChat = p.title.toLowerCase().startsWith('chat');
              const iconName = isPdf ? 'picture_as_pdf' : isChat ? 'chat' : 'article';

              return (
                <div
                  key={p.id}
                  onClick={() => onSelectProject(p)}
                  className="flex items-center p-3 rounded-xl hover:bg-[#27272A] transition-colors cursor-pointer group"
                >
                  <div className="mr-4 text-[#76777D] group-hover:text-[#F4F4F5] transition-colors shrink-0">
                    <span className="material-symbols-outlined text-[20px]" style={!isPdf && !isChat ? { fontVariationSettings: "'FILL' 1" } : {}}>
                      {iconName}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="text-[14px] font-medium text-[#F4F4F5] truncate">
                      {p.title}
                    </h4>
                    <p className="text-[13px] text-[#A1A1AA] truncate">
                      {p.description}
                    </p>
                  </div>

                  <div className="hidden sm:flex items-center gap-3 ml-4 text-[12px] text-[#76777D] shrink-0">
                    <span>{p.dateLabel}</span>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenBibliography(p);
                    }}
                    className="ml-4 p-2 rounded-lg text-[#76777D] hover:text-[#10B981] hover:bg-[#3F3F46] opacity-0 group-hover:opacity-100 transition-all shrink-0"
                    title="View Sources"
                  >
                    <span className="material-symbols-outlined text-[18px]">download</span>
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
};
