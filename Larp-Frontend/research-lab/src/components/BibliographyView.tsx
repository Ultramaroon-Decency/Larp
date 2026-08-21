// src/components/BibliographyView.tsx
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
    <div className="flex-1 overflow-y-auto p-4 md:p-8 bg-[#090D16] text-[#E5E7EB]">
      <div className="max-w-[760px] mx-auto w-full space-y-8">
        {/* Page Header & Global Actions */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-[#1B2536] pb-6">
          <div>
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1.5">
              {project.category} • {project.sources.length} Verified Sources
            </div>
            <h2 className="text-[20px] font-bold text-white tracking-tight m-0 mb-1.5">
              Sources & Bibliography
            </h2>
            <p className="text-zinc-400 text-[13px] m-0 max-w-xl leading-relaxed">
              A compiled list of peer-reviewed sources utilized in this research synthesis. Sorted by relevance score.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              onClick={() => onDownloadBibtex(project.sources, project.title)}
              className="h-8.5 px-3 bg-[#0D1525] border border-[#1B2536] text-zinc-300 text-[11px] font-bold uppercase tracking-wider rounded-lg hover:border-zinc-700 hover:text-white transition-all flex items-center gap-1.5 cursor-pointer outline-none"
            >
              <span className="material-symbols-outlined text-[15px]">download</span>
              Download BibTeX
            </button>
            <button
              onClick={handleExportZotero}
              className="h-8.5 px-3 bg-[#0D1525] border border-[#1B2536] text-zinc-300 text-[11px] font-bold uppercase tracking-wider rounded-lg hover:border-zinc-700 hover:text-white transition-all flex items-center gap-1.5 cursor-pointer outline-none"
            >
              <span className="material-symbols-outlined text-[15px]">import_export</span>
              Export Zotero RIS
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
                className="bg-[#0D1525] border border-[#1B2536] rounded-xl p-4.5 hover:border-primary/50 transition-colors group flex flex-col relative shadow-sm"
              >
                <div className="flex justify-between items-start mb-3.5 gap-3">
                  <h3 className="text-[14px] font-bold text-white m-0 leading-snug line-clamp-2 pr-2 group-hover:text-primary transition-colors">
                    {source.url ? (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        className="outline-none hover:underline"
                      >
                        {source.title}
                      </a>
                    ) : (
                      source.title
                    )}
                  </h3>
                  <div className="shrink-0 bg-primary/10 border border-primary/25 text-primary px-2 py-0.5 rounded-md text-[10px] font-bold font-mono flex items-center gap-1">
                    <span className="material-symbols-outlined text-[12px]">verified</span>
                    {relPercent}% Rel
                  </div>
                </div>

                <div className="text-[12px] text-zinc-400 mb-4 flex-grow flex flex-col gap-1">
                  <div>
                    <strong className="font-semibold text-zinc-500 mr-1">Authors:</strong> {source.authors}
                  </div>
                  <div>
                    <strong className="font-semibold text-zinc-500 mr-1">Year:</strong> {source.year}
                  </div>
                  <div className="truncate">
                    <strong className="font-semibold text-zinc-500 mr-1">Journal:</strong> {source.journal}
                  </div>
                </div>

                <div className="border-t border-[#1B2536] pt-3 flex justify-between items-center mt-auto z-10">
                  <div className="flex flex-wrap gap-1">
                    {source.doi && (
                      <span className="inline-flex items-center px-1.5 py-0.5 bg-[#070B13] text-zinc-500 rounded text-[9px] font-bold uppercase tracking-wider font-mono">
                        DOI: {source.doi}
                      </span>
                    )}
                    {source.tags.map((t) => (
                      <span
                        key={t}
                        className="inline-flex items-center px-1.5 py-0.5 bg-[#070B13] text-zinc-400 rounded text-[9px] font-bold uppercase tracking-wider"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={() => {
                      if (source.url) window.open(source.url, '_blank');
                    }}
                    className="text-zinc-500 hover:text-white p-1 rounded hover:bg-zinc-800 outline-none shrink-0"
                    title="Open Source Link"
                  >
                    <span className="material-symbols-outlined text-[16px]">open_in_new</span>
                  </button>
                </div>
              </article>
            );
          })}
        </div>

        {/* Load Remaining Sources Pagination */}
        {project.sources.length > 6 && !showAll && (
          <div className="mt-8 flex justify-center border-t border-[#1B2536] pt-6">
            <button
              onClick={() => setShowAll(true)}
              className="h-9 px-4 bg-[#0D1525] border border-[#1B2536] text-zinc-300 hover:text-white hover:border-zinc-700 text-[11px] font-bold uppercase tracking-wider rounded-lg transition-all cursor-pointer shadow-sm outline-none"
            >
              Load Remaining Sources ({project.sources.length - 6} more)
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
