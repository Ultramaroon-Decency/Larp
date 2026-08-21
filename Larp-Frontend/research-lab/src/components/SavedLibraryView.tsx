// src/components/SavedLibraryView.tsx
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
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

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
    <div className="flex-1 overflow-y-auto p-4 md:p-8 bg-[#090D16] text-[#E5E7EB]">
      <div className="max-w-[760px] mx-auto space-y-8">
        {/* Filters & View Mode Controls */}
        <div className="flex flex-wrap gap-4 items-center justify-between border-b border-[#1B2536] pb-4">
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider rounded-lg border transition-all cursor-pointer outline-none ${
                filter === 'all'
                  ? 'bg-primary text-white border-primary'
                  : 'bg-[#0D1525] text-zinc-400 border-[#1B2536] hover:text-white'
              }`}
            >
              All Projects
            </button>
            <button
              onClick={() => setFilter('recent')}
              className={`px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer outline-none ${
                filter === 'recent'
                  ? 'bg-primary text-white border-primary'
                  : 'bg-[#0D1525] text-zinc-400 border-[#1B2536] hover:text-white'
              }`}
            >
              <span className="material-symbols-outlined text-[14px]">schedule</span>
              Recent
            </button>
            <button
              onClick={() => setFilter('starred')}
              className={`px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer outline-none ${
                filter === 'starred'
                  ? 'bg-primary text-white border-primary'
                  : 'bg-[#0D1525] text-zinc-400 border-[#1B2536] hover:text-white'
              }`}
            >
              <span className="material-symbols-outlined text-[14px]">star</span>
              Starred
            </button>
            <button
              onClick={() => setFilter('shared')}
              className={`px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer outline-none ${
                filter === 'shared'
                  ? 'bg-primary text-white border-primary'
                  : 'bg-[#0D1525] text-zinc-400 border-[#1B2536] hover:text-white'
              }`}
            >
              <span className="material-symbols-outlined text-[14px]">group</span>
              Shared
            </button>
          </div>

          <div className="flex gap-2 items-center">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-colors outline-none cursor-pointer ${
                viewMode === 'grid'
                  ? 'bg-[#172237] text-primary'
                  : 'text-zinc-500 hover:text-white'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">grid_view</span>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition-colors outline-none cursor-pointer ${
                viewMode === 'list'
                  ? 'bg-[#172237] text-primary'
                  : 'text-zinc-500 hover:text-white'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">view_list</span>
            </button>
          </div>
        </div>

        {/* Section: Collections (Quiet Grid) */}
        <section className="space-y-3">
          <h3 className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[15px]">folder</span>
            Collections
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {collections.map((col) => (
              <div
                key={col.id}
                onClick={() => {
                  const matched = projects.find((p) => col.projectIds.includes(p.id)) || projects[0];
                  if (matched) onOpenBibliography(matched);
                }}
                className="bg-[#0D1525] border border-[#1B2536] rounded-xl p-4.5 hover:border-primary/50 cursor-pointer transition-all group relative overflow-hidden flex flex-col justify-between h-28 shadow-sm"
              >
                <div className="absolute top-0 right-0 p-3 opacity-[0.02] group-hover:opacity-[0.08] transition-opacity z-0">
                  <span className="material-symbols-outlined text-[56px] text-white">
                    {col.icon}
                  </span>
                </div>
                <div className="flex justify-between items-start z-10 min-w-0">
                  <h4 className="font-bold text-[14px] text-white group-hover:text-primary transition-colors truncate pr-3">
                    {col.title}
                  </h4>
                  <button className="text-zinc-500 hover:text-white outline-none shrink-0" onClick={(e) => e.stopPropagation()}>
                    <span className="material-symbols-outlined text-[16px]">more_horiz</span>
                  </button>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-zinc-400 z-10">
                  <span className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[13px] text-zinc-500">description</span>
                    {col.refsCount} refs
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[13px] text-zinc-500">update</span>
                    {col.updatedAgo}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Divider */}
        <div className="h-px bg-[#1B2536] w-full" />

        {/* Section: Recent Documents & Drafts */}
        <section className="space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[15px]">draft</span>
              Recent Documents & Drafts
            </h3>
            <span className="text-[11px] text-primary hover:underline cursor-pointer font-semibold">
              View All ({filteredProjects.length})
            </span>
          </div>

          <div className="flex flex-col border border-[#1B2536] rounded-xl bg-[#0D1525] overflow-hidden divide-y divide-zinc-900 shadow-sm">
            {filteredProjects.map((p) => {
              const isPdf = p.title.toLowerCase().endsWith('.pdf');
              const isChat = p.title.toLowerCase().startsWith('chat');
              const iconName = isPdf ? 'picture_as_pdf' : isChat ? 'chat' : 'article';
              const badgeLabel = p.status === 'draft' ? 'Draft' : isPdf ? 'Source' : 'Session';

              return (
                <div
                  key={p.id}
                  onClick={() => onSelectProject(p)}
                  className="flex items-center p-3.5 hover:bg-[#131E31]/40 transition-colors cursor-pointer group"
                >
                  <div className="mr-3.5 text-zinc-500 group-hover:text-primary transition-colors shrink-0">
                    <span className="material-symbols-outlined text-[20px]" style={!isPdf && !isChat ? { fontVariationSettings: "'FILL' 1" } : {}}>
                      {iconName}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="text-[14px] text-white font-medium truncate">
                      {p.title}
                    </h4>
                    <p className="text-[11px] text-zinc-400 truncate mt-0.5">
                      {p.description}
                    </p>
                  </div>

                  <div className="hidden sm:flex items-center gap-3.5 ml-4 text-[11px] text-zinc-400 shrink-0">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                        p.status === 'draft' || isChat
                          ? 'bg-primary/10 text-primary border-primary/25'
                          : 'bg-[#172237] text-zinc-300 border-[#1B2536]'
                      }`}
                    >
                      {badgeLabel}
                    </span>
                    <span className="font-mono text-zinc-500">{p.dateLabel}</span>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenBibliography(p);
                    }}
                    className="ml-4 text-zinc-500 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity outline-none cursor-pointer shrink-0"
                    title="View Citations"
                  >
                    <span className="material-symbols-outlined text-[16px]">download</span>
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
