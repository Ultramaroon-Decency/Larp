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
    <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#F7F9FB]">
      <div className="max-w-[840px] mx-auto space-y-8">
        {/* Filters & View Mode Controls */}
        <div className="flex flex-wrap gap-4 items-center justify-between border-b border-[#C6C6CD]/60 pb-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-1.5 text-[13px] font-bold rounded-md border transition-colors cursor-pointer ${
                filter === 'all'
                  ? 'bg-[#0F172A] text-white border-[#0F172A]'
                  : 'bg-white text-[#45464D] border-[#C6C6CD] hover:bg-[#E0E3E5]'
              }`}
            >
              All Projects
            </button>
            <button
              onClick={() => setFilter('recent')}
              className={`px-4 py-1.5 text-[13px] font-bold rounded-md border transition-colors flex items-center gap-1.5 cursor-pointer ${
                filter === 'recent'
                  ? 'bg-[#0F172A] text-white border-[#0F172A]'
                  : 'bg-white text-[#45464D] border-[#C6C6CD] hover:bg-[#E0E3E5]'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">schedule</span>
              Recent
            </button>
            <button
              onClick={() => setFilter('starred')}
              className={`px-4 py-1.5 text-[13px] font-bold rounded-md border transition-colors flex items-center gap-1.5 cursor-pointer ${
                filter === 'starred'
                  ? 'bg-[#0F172A] text-white border-[#0F172A]'
                  : 'bg-white text-[#45464D] border-[#C6C6CD] hover:bg-[#E0E3E5]'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">star</span>
              Starred
            </button>
            <button
              onClick={() => setFilter('shared')}
              className={`px-4 py-1.5 text-[13px] font-bold rounded-md border transition-colors flex items-center gap-1.5 cursor-pointer ${
                filter === 'shared'
                  ? 'bg-[#0F172A] text-white border-[#0F172A]'
                  : 'bg-white text-[#45464D] border-[#C6C6CD] hover:bg-[#E0E3E5]'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">group</span>
              Shared
            </button>
          </div>

          <div className="flex gap-2 items-center">
            <div className="h-6 border-l border-[#C6C6CD] mx-1" />
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-md transition-colors ${
                viewMode === 'grid'
                  ? 'bg-[#0F172A] text-white'
                  : 'text-[#45464D] hover:bg-[#E0E3E5]'
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">grid_view</span>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-md transition-colors ${
                viewMode === 'list'
                  ? 'bg-[#0F172A] text-white'
                  : 'text-[#45464D] hover:bg-[#E0E3E5]'
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">view_list</span>
            </button>
          </div>
        </div>

        {/* Section: Collections (Bento Grid) */}
        <section>
          <h3 className="text-[11px] font-bold tracking-wider text-[#45464D] uppercase mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">folder</span>
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
                className="bg-white border border-[#C6C6CD] rounded-lg p-5 hover:border-[#0F172A] cursor-pointer transition-all group relative overflow-hidden flex flex-col h-32 shadow-2xs"
              >
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <span className="material-symbols-outlined text-[64px] text-[#0F172A]">
                    {col.icon}
                  </span>
                </div>
                <div className="flex justify-between items-start mb-auto z-10">
                  <h4 className="font-bold text-[18px] text-[#0F172A] group-hover:text-[#2563EB] transition-colors truncate pr-4 leading-tight">
                    {col.title}
                  </h4>
                  <button className="text-[#45464D] hover:text-[#0F172A] z-20">
                    <span className="material-symbols-outlined text-[18px]">more_horiz</span>
                  </button>
                </div>
                <div className="flex items-center gap-4 text-[13px] font-medium text-[#45464D] z-10 mt-4">
                  <span className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">description</span>
                    {col.refsCount} refs
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">update</span>
                    {col.updatedAgo}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <div className="h-px bg-[#C6C6CD] w-full my-6" />

        {/* Section: Recent Documents & Drafts */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-[11px] font-bold tracking-wider text-[#45464D] uppercase flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">draft</span>
              Recent Documents & Drafts
            </h3>
            <span className="text-[13px] font-bold text-[#0F172A] hover:underline cursor-pointer">
              View All ({filteredProjects.length})
            </span>
          </div>

          <div className="flex flex-col border border-[#C6C6CD] rounded-lg bg-white overflow-hidden shadow-2xs divide-y divide-[#C6C6CD]/50">
            {filteredProjects.map((p) => {
              const isPdf = p.title.toLowerCase().endsWith('.pdf');
              const isChat = p.title.toLowerCase().startsWith('chat');
              const iconName = isPdf ? 'picture_as_pdf' : isChat ? 'chat' : 'article';
              const badgeLabel = p.status === 'draft' ? 'Draft' : isPdf ? 'Source' : 'Session';

              return (
                <div
                  key={p.id}
                  onClick={() => onSelectProject(p)}
                  className="flex items-center p-4 hover:bg-[#F2F4F6] transition-colors cursor-pointer group"
                >
                  <div className="mr-4 text-[#45464D] group-hover:text-[#0F172A] transition-colors">
                    <span className="material-symbols-outlined text-[24px]">
                      {iconName}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="text-[16px] text-[#0F172A] font-bold truncate group-hover:text-[#2563EB] transition-colors">
                      {p.title}
                    </h4>
                    <p className="text-[13px] text-[#45464D] truncate mt-0.5">
                      {p.description}
                    </p>
                  </div>

                  <div className="hidden sm:flex items-center gap-3 ml-4 text-[13px] text-[#45464D]">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold border ${
                        p.status === 'draft'
                          ? 'bg-[#EFF6FF] text-[#0F172A] border-[#EFF6FF]'
                          : 'bg-[#E0E3E5] text-[#191C1E] border-[#C6C6CD]'
                      }`}
                    >
                      {badgeLabel}
                    </span>
                    <span className="font-mono text-[12px]">{p.dateLabel}</span>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenBibliography(p);
                    }}
                    className="ml-4 text-[#45464D] hover:text-[#0F172A] opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity p-1"
                    title="View Sources & Citations"
                  >
                    <span className="material-symbols-outlined">download</span>
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
