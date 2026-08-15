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
    ? sources.filter((s) => s.tags.includes(filterTag))
    : sources;

  const handleBibliographyClick = () => {
    onViewBibliographyClick();
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  const panelBody = (
    <>
      {/* Panel Header */}
      <div className="p-4 border-b border-[#C6C6CD] flex items-center justify-between bg-[#F7F9FB] shrink-0">
        <div className="flex items-center gap-2">
          <h3 className="font-bold text-[18px] text-[#0F172A]">Sources & Citations</h3>
          <span className="text-[11px] font-bold bg-[#E0E3E5] px-2 py-0.5 rounded-full text-[#45464D]">
            {sources.length}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleBibliographyClick}
            className="text-[#45464D] hover:text-[#0F172A] text-[12px] font-bold uppercase tracking-wider transition-colors flex items-center gap-1 cursor-pointer"
            title="Full Bibliography View"
          >
            <span className="material-symbols-outlined text-[18px]">filter_list</span>
          </button>
          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="md:hidden text-[#45464D] hover:text-[#0F172A] p-1 rounded-md hover:bg-[#E0E3E5] transition-colors cursor-pointer"
              title="Close Sources"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          )}
        </div>
      </div>

      {/* Sources Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {filteredSources.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-[#76777D]">
            <span className="material-symbols-outlined text-[36px] mb-2">auto_stories</span>
            <p className="text-[13px] font-medium">
              {sources.length === 0
                ? 'Sources will appear here after synthesis completes.'
                : 'No sources match the selected tag.'}
            </p>
            {filterTag && (
              <button
                onClick={() => setFilterTag(null)}
                className="mt-2 text-[12px] text-[#2563EB] hover:underline"
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
              className={`bg-white border rounded-md p-4 flex flex-col gap-2 transition-all cursor-pointer group shadow-2xs ${
                isHighlighted
                  ? 'border-[#0F172A] ring-2 ring-[#0F172A]/20 bg-[#EFF6FF]'
                  : 'border-[#C6C6CD] hover:border-[#0F172A]'
              }`}
            >
              {/* Header: Index badge and Relevance score */}
              <div className="flex justify-between items-start">
                <span className="inline-flex items-center justify-center bg-[#0F172A] text-white rounded-md px-2 py-0.5 text-[12px] font-bold font-mono">
                  [{source.index}]
                </span>
                <span className="font-mono text-[11px] font-bold text-[#45464D] group-hover:text-[#0F172A] transition-colors">
                  Relevance: {(typeof source.relevance === 'number' && !isNaN(source.relevance) ? source.relevance : 0).toFixed(2)}
                </span>
              </div>

              {/* Title */}
              <h4 className="font-bold text-[15px] text-[#0F172A] leading-snug group-hover:text-[#2563EB] transition-colors">
                {source.title}
              </h4>

              {/* Journal / Date */}
              <p className="text-[13px] text-[#45464D]">
                {source.journal}
              </p>

              {/* Abstract Preview if available */}
              {source.abstract && (
                <p className="text-[12px] text-[#76777D] line-clamp-2 italic">
                  &ldquo;{source.abstract}&rdquo;
                </p>
              )}

              {/* Tags & Action links */}
              <div className="mt-2 flex flex-wrap gap-1.5 items-center">
                {source.tags.map((tag) => (
                  <span
                    key={tag}
                    onClick={(e) => {
                      e.stopPropagation();
                      setFilterTag(filterTag === tag ? null : tag);
                    }}
                    className={`border border-[#C6C6CD] rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#45464D] transition-colors cursor-pointer ${
                      filterTag === tag ? 'bg-[#0F172A] text-white' : 'hover:bg-[#E0E3E5]'
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
                    className="ml-auto text-[#2563EB] hover:underline text-[11px] font-medium flex items-center gap-0.5"
                  >
                    View
                    <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                  </a>
                )}
              </div>
            </div>
          );
        })}

        {/* View Full Bibliography CTA */}
        <button
          onClick={handleBibliographyClick}
          className="w-full py-2.5 border border-[#C6C6CD] rounded-md text-[12px] font-bold uppercase tracking-wider text-[#0F172A] hover:bg-[#E0E3E5] transition-colors flex items-center justify-center gap-2 mt-2 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[16px]">book</span>
          Open Bibliography Page
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop Rail */}
      <aside className="w-[300px] h-full bg-[#F2F4F6] border-l border-[#C6C6CD] flex flex-col shrink-0 hidden md:flex">
        {panelBody}
      </aside>

      {/* Mobile Overlay & Drawer */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 md:hidden flex justify-end">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-xs"
            onClick={onCloseMobile}
          />
          <aside className="relative w-[320px] max-w-[85vw] h-full bg-[#F2F4F6] border-l border-[#C6C6CD] flex flex-col z-10 shadow-2xl">
            {panelBody}
          </aside>
        </div>
      )}
    </>
  );
};
