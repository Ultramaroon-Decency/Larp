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
    <div className="flex-1 overflow-y-auto p-margin-page bg-surface">
      <div className="max-w-container-max mx-auto space-y-8">
        {/* Filters & View Mode Controls */}
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-1.5 text-citation font-citation rounded-DEFAULT border transition-colors cursor-pointer ${
                filter === 'all'
                  ? 'bg-primary text-on-primary border-primary'
                  : 'bg-surface text-on-surface-variant border-outline-variant hover:bg-surface-variant'
              }`}
            >
              All Projects
            </button>
            <button
              onClick={() => setFilter('recent')}
              className={`px-4 py-1.5 text-citation font-citation rounded-DEFAULT border transition-colors flex items-center gap-1.5 cursor-pointer ${
                filter === 'recent'
                  ? 'bg-primary text-on-primary border-primary'
                  : 'bg-surface text-on-surface-variant border-outline-variant hover:bg-surface-variant'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">schedule</span>
              Recent
            </button>
            <button
              onClick={() => setFilter('starred')}
              className={`px-4 py-1.5 text-citation font-citation rounded-DEFAULT border transition-colors flex items-center gap-1.5 cursor-pointer ${
                filter === 'starred'
                  ? 'bg-primary text-on-primary border-primary'
                  : 'bg-surface text-on-surface-variant border-outline-variant hover:bg-surface-variant'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">star</span>
              Starred
            </button>
            <button
              onClick={() => setFilter('shared')}
              className={`px-4 py-1.5 text-citation font-citation rounded-DEFAULT border transition-colors flex items-center gap-1.5 cursor-pointer ${
                filter === 'shared'
                  ? 'bg-primary text-on-primary border-primary'
                  : 'bg-surface text-on-surface-variant border-outline-variant hover:bg-surface-variant'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">group</span>
              Shared
            </button>
          </div>

          <div className="flex gap-2 items-center">
            <div className="h-8 border-l border-outline-variant mx-2" />
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-DEFAULT transition-colors ${
                viewMode === 'grid'
                  ? 'bg-surface-variant text-primary hover:bg-outline-variant'
                  : 'text-on-surface-variant hover:bg-surface-variant'
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">grid_view</span>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-DEFAULT transition-colors ${
                viewMode === 'list'
                  ? 'bg-surface-variant text-primary hover:bg-outline-variant'
                  : 'text-on-surface-variant hover:bg-surface-variant'
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">view_list</span>
            </button>
          </div>
        </div>

        {/* Section: Collections (Bento Grid) */}
        <section>
          <h3 className="font-label-caps text-label-caps text-on-surface-variant mb-4 flex items-center gap-2">
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
                className="bg-surface-container-lowest border border-outline-variant rounded-lg p-5 hover:border-primary cursor-pointer transition-colors group relative overflow-hidden flex flex-col h-32"
              >
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <span className="material-symbols-outlined text-[64px] text-primary">
                    {col.icon}
                  </span>
                </div>
                <div className="flex justify-between items-start mb-auto z-10">
                  <h4 className="font-headline-md text-headline-md text-on-background group-hover:text-primary transition-colors truncate pr-4">
                    {col.title}
                  </h4>
                  <button className="text-on-surface-variant hover:text-primary z-20">
                    <span className="material-symbols-outlined text-[18px]">more_horiz</span>
                  </button>
                </div>
                <div className="flex items-center gap-4 text-citation font-citation text-on-surface-variant z-10 mt-4">
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

        <div className="h-px bg-outline-variant w-full my-8" />

        {/* Section: Recent Documents & Drafts */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-label-caps text-label-caps text-on-surface-variant flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">draft</span>
              Recent Documents & Drafts
            </h3>
            <span className="text-citation text-primary hover:underline cursor-pointer">
              View All ({filteredProjects.length})
            </span>
          </div>

          <div className="flex flex-col border border-outline-variant rounded-lg bg-surface-container-lowest overflow-hidden">
            {filteredProjects.map((p) => {
              const isPdf = p.title.toLowerCase().endsWith('.pdf');
              const isChat = p.title.toLowerCase().startsWith('chat');
              const iconName = isPdf ? 'picture_as_pdf' : isChat ? 'chat' : 'article';
              const badgeLabel = p.status === 'draft' ? 'Draft' : isPdf ? 'Source' : 'Session';

              return (
                <div
                  key={p.id}
                  onClick={() => onSelectProject(p)}
                  className="flex items-center p-4 border-b border-outline-variant hover:bg-surface-variant/30 transition-colors cursor-pointer group"
                >
                  <div className="mr-4 text-on-surface-variant group-hover:text-primary transition-colors">
                    <span className="material-symbols-outlined" style={!isPdf && !isChat ? { fontVariationSettings: "'FILL' 1" } : {}}>
                      {iconName}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="font-body-lg text-body-lg text-on-background font-medium truncate">
                      {p.title}
                    </h4>
                    <p className="text-citation font-citation text-on-surface-variant truncate">
                      {p.description}
                    </p>
                  </div>

                  <div className="hidden sm:flex items-center gap-3 ml-4 text-citation text-on-surface-variant">
                    <span
                      className={`px-2 py-0.5 rounded-DEFAULT border ${
                        p.status === 'draft' || isChat
                          ? 'bg-[#EFF6FF] text-primary border-[#EFF6FF]'
                          : 'bg-surface-variant text-on-surface border-outline-variant'
                      }`}
                    >
                      {badgeLabel}
                    </span>
                    <span>{p.dateLabel}</span>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenBibliography(p);
                    }}
                    className="ml-4 text-on-surface-variant hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity"
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
