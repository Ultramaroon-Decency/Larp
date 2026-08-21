// src/components/SourcesPanel.tsx
import React, { useState } from 'react';
import { Source } from '../types';

interface SourcesPanelProps {
  sources: Source[];
  highlightedSourceIndex: number | null;
  onSourceHover: (index: number | null) => void;
  onViewBibliographyClick: () => void;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

export const SourcesPanel: React.FC<SourcesPanelProps> = ({
  sources,
  highlightedSourceIndex,
  onSourceHover,
  onViewBibliographyClick,
  isOpenMobile = false,
  onCloseMobile
}) => {
  const [filterTag, setFilterTag] = useState<string | null>(null);

  const filteredSources = filterTag
    ? sources.filter((s) => s.tags?.includes(filterTag))
    : sources;

  const handleBibliographyClick = () => {
    onViewBibliographyClick();
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  const panelBody = (
    <div className="flex flex-col h-full bg-[#0D1626] border-l border-[#1B2536] text-[#E5E7EB]">
      {/* Panel Header */}
      <div className="p-4 border-b border-[#1B2536] flex items-center justify-between bg-black/10 shrink-0">
        <div className="flex items-center gap-2">
          <h3 className="font-bold text-[14px] text-white">Sources</h3>
          <span className="text-[10px] font-bold bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full text-primary">
            {sources.length}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleBibliographyClick}
            className="text-zinc-400 hover:text-white p-1 transition-colors flex items-center justify-center outline-none cursor-pointer"
            title="Full Bibliography View"
          >
            <span className="material-symbols-outlined text-[18px]">filter_list</span>
          </button>
          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="md:hidden text-zinc-400 hover:text-white p-1 rounded-md hover:bg-zinc-900 transition-colors cursor-pointer outline-none"
              title="Close Sources"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          )}
        </div>
      </div>

      {/* Sources Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3.5 flex flex-col gap-3">
        {filteredSources.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-zinc-500">
            <span className="material-symbols-outlined text-[28px] mb-1">auto_stories</span>
            <p className="text-[12px]">
              {sources.length === 0
                ? 'Sources will appear here after synthesis completes.'
                : 'No sources match the selected tag.'}
            </p>
            {filterTag && (
              <button
                onClick={() => setFilterTag(null)}
                className="mt-2 text-[11px] text-primary hover:underline outline-none"
              >
                Clear filter
              </button>
            )}
          </div>
        )}

        {filteredSources.map((source) => {
          const isHighlighted = highlightedSourceIndex === source.index;

          return (
            <div
              key={source.id}
              onMouseEnter={() => onSourceHover(source.index)}
              onMouseLeave={() => onSourceHover(null)}
              className={`border rounded-xl p-3.5 flex flex-col gap-2 transition-all cursor-pointer group shadow-2xs ${
                isHighlighted
                  ? 'border-primary bg-[#131E35] ring-2 ring-primary/10'
                  : 'border-[#1B2536] bg-[#070B13] hover:border-zinc-700'
              }`}
            >
              {/* Header: Index badge and Relevance score */}
              <div className="flex justify-between items-start">
                <span className="inline-flex items-center justify-center bg-primary text-white rounded px-1.5 py-0.5 text-[10px] font-bold font-mono">
                  [{source.index}]
                </span>
                <span className="font-mono text-[9px] font-semibold text-zinc-500 group-hover:text-primary transition-colors">
                  Relevance: {(typeof source.relevance === 'number' && !isNaN(source.relevance) ? source.relevance : 0).toFixed(2)}
                </span>
              </div>

              {/* Title */}
              <h4 className="font-semibold text-[13px] text-white leading-snug group-hover:text-primary transition-colors line-clamp-2">
                {source.title}
              </h4>

              {/* Journal / Date */}
              <p className="text-[11px] text-zinc-400 truncate">
                {source.journal}
              </p>

              {/* Abstract Preview if available */}
              {source.abstract && (
                <p className="text-[10px] text-zinc-500 line-clamp-2 italic leading-relaxed">
                  &ldquo;{source.abstract}&rdquo;
                </p>
              )}

              {/* Tags & Action links */}
              <div className="mt-1 flex flex-wrap gap-1 items-center">
                {(source.tags || []).map((tag) => (
                  <span
                    key={tag}
                    onClick={(e) => {
                      e.stopPropagation();
                      setFilterTag(filterTag === tag ? null : tag);
                    }}
                    className={`border border-[#1B2536] rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-zinc-400 transition-colors cursor-pointer select-none ${
                      filterTag === tag ? 'bg-primary text-white border-primary' : 'hover:bg-zinc-800'
                    }`}
                  >
                    {tag}
                  </span>
                ))}
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="ml-auto text-primary hover:underline text-[10px] font-medium flex items-center gap-0.5"
                  >
                    View
                    <span className="material-symbols-outlined text-[10px]">open_in_new</span>
                  </a>
                )}
              </div>
            </div>
          );
        })}

        {/* View Full Bibliography CTA */}
        <button
          onClick={handleBibliographyClick}
          className="w-full py-2 border border-[#1B2536] hover:border-zinc-700 bg-zinc-900 rounded-lg text-[11px] font-bold uppercase tracking-wider text-zinc-300 hover:text-white transition-all flex items-center justify-center gap-2 mt-2 cursor-pointer outline-none"
        >
          <span className="material-symbols-outlined text-[14px]">book</span>
          Open Bibliography Page
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Rail */}
      <aside className="w-[280px] h-full flex flex-col shrink-0 hidden md:flex">
        {panelBody}
      </aside>

      {/* Mobile Overlay & Drawer */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 md:hidden flex justify-end">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs"
            onClick={onCloseMobile}
          />
          <aside className="relative w-[300px] max-w-[85vw] h-full flex flex-col z-10 shadow-2xl">
            {panelBody}
          </aside>
        </div>
      )}
    </>
  );
};
