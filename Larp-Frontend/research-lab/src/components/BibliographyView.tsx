import React, { useState } from 'react';
import { ResearchProject, Source } from '../types';

interface BibliographyViewProps {
  project: ResearchProject;
  onDownloadBibtex: (sources: Source[], title: string) => void;
}

export const BibliographyView: React.FC<BibliographyViewProps> = ({
  project,
  onDownloadBibtex
}) => {
  const [showAll, setShowAll] = useState(false);

  const sourcesToDisplay = showAll
    ? project.sources
    : project.sources.slice(0, 6);

  const handleExportZotero = () => {
    const risText = project.sources
      .map(
        (s) =>
          `TY  - JOUR\nTI  - ${s.title}\nAU  - ${s.authors}\nPY  - ${s.year}\nJO  - ${s.journal}\nDO  - ${s.doi}\nER  -\n`
      )
      .join('\n');

    const blob = new Blob([risText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${project.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}_zotero.ris`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#F7F9FB]">
      <div className="max-w-[840px] mx-auto w-full space-y-8">
        {/* Page Header & Global Actions */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-[#C6C6CD] pb-6">
          <div>
            <div className="text-[12px] font-bold text-[#45464D] uppercase tracking-wider mb-1">
              {project.category} • {project.sources.length} Verified Sources
            </div>
            <h2 className="text-[26px] md:text-[28px] font-bold text-[#0F172A] tracking-tight m-0 mb-2">
              Sources & Bibliography
            </h2>
            <p className="text-[#45464D] text-[15px] m-0 max-w-2xl leading-relaxed">
              A compiled list of {project.sources.length} peer-reviewed sources utilized in current synthesis. Sorted by relevance score.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              onClick={() => onDownloadBibtex(project.sources, project.title)}
              className="h-9 px-4 border border-[#C6C6CD] bg-white text-[#0F172A] text-[13px] font-bold rounded-md hover:bg-[#E0E3E5] transition-colors flex items-center gap-2 cursor-pointer shadow-2xs"
            >
              <span className="material-symbols-outlined text-[18px]">download</span>
              Download BibTeX
            </button>
            <button
              onClick={handleExportZotero}
              className="h-9 px-4 border border-[#C6C6CD] bg-white text-[#0F172A] text-[13px] font-bold rounded-md hover:bg-[#E0E3E5] transition-colors flex items-center gap-2 cursor-pointer shadow-2xs"
            >
              <span className="material-symbols-outlined text-[18px]">import_export</span>
              Export to Zotero
            </button>
          </div>
        </div>

        {/* Database Grid Layout for Sources */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sourcesToDisplay.map((source) => {
            const relPercent = Math.round(source.relevance * 100);

            return (
              <article
                key={source.id}
                className="bg-white border border-[#C6C6CD] rounded-md p-5 hover:border-[#0F172A] transition-colors group flex flex-col relative shadow-2xs"
              >
                <div className="flex justify-between items-start mb-3 gap-2">
                  <h3 className="text-[16px] font-bold text-[#0F172A] m-0 leading-snug line-clamp-2 pr-2 group-hover:text-[#2563EB] transition-colors">
                    <a
                      href={source.url || '#'}
                      target="_blank"
                      rel="noreferrer"
                      className="outline-none"
                    >
                      {source.title}
                    </a>
                  </h3>
                  <div className="shrink-0 bg-blue-50 border border-blue-100 text-[#003EA8] px-2 py-0.5 rounded text-[12px] font-bold font-mono flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">verified</span>
                    {relPercent}% Rel
                  </div>
                </div>

                <div className="text-[13px] text-[#45464D] mb-4 flex-grow flex flex-col gap-1">
                  <div>
                    <strong className="font-semibold text-[#0F172A]">Authors:</strong> {source.authors}
                  </div>
                  <div>
                    <strong className="font-semibold text-[#0F172A]">Year:</strong> {source.year}
                  </div>
                  <div className="truncate">
                    <strong className="font-semibold text-[#0F172A]">Journal:</strong> {source.journal}
                  </div>
                </div>

                <div className="border-t border-[#C6C6CD]/60 pt-3 flex justify-between items-center mt-auto z-10">
                  <div className="flex flex-wrap gap-1.5">
                    {source.doi && (
                      <span className="inline-flex items-center px-2 py-0.5 bg-[#ECEEF0] text-[#45464D] rounded text-[10px] font-bold uppercase tracking-wider font-mono">
                        DOI: {source.doi}
                      </span>
                    )}
                    {source.tags.map((t) => (
                      <span
                        key={t}
                        className="inline-flex items-center px-2 py-0.5 bg-[#ECEEF0] text-[#45464D] rounded text-[10px] font-bold uppercase tracking-wider"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={() => {
                      if (source.url) window.open(source.url, '_blank');
                    }}
                    className="text-[#45464D] hover:text-[#0F172A] p-1 rounded hover:bg-[#E0E3E5]"
                    title="Open Source Link"
                  >
                    <span className="material-symbols-outlined text-[18px]">open_in_new</span>
                  </button>
                </div>
              </article>
            );
          })}
        </div>

        {/* Load Remaining Sources Pagination */}
        {project.sources.length > 6 && !showAll && (
          <div className="mt-8 flex justify-center border-t border-[#C6C6CD]/60 pt-6">
            <button
              onClick={() => setShowAll(true)}
              className="h-10 px-6 bg-white border border-[#C6C6CD] text-[#0F172A] text-[13px] font-bold uppercase tracking-wider rounded-md hover:bg-[#E0E3E5] transition-colors cursor-pointer shadow-2xs"
            >
              Load Remaining Sources ({project.sources.length - 6} more)
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
