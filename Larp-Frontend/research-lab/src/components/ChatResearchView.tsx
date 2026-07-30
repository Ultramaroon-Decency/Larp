import React, { useState } from 'react';
import { ResearchProject, Source } from '../types';
import { SourcesPanel } from './SourcesPanel';

interface ChatResearchViewProps {
  project: ResearchProject;
  onRefineQuery: (refineText: string) => void;
  onViewBibliographyClick: () => void;
  isSynthesizing: boolean;
}

export const ChatResearchView: React.FC<ChatResearchViewProps> = ({
  project,
  onRefineQuery,
  onViewBibliographyClick,
  isSynthesizing
}) => {
  const [refineText, setRefineText] = useState('');
  const [highlightedSourceIndex, setHighlightedSourceIndex] = useState<number | null>(null);

  const handleRefineSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!refineText.trim() || isSynthesizing) return;
    onRefineQuery(refineText);
    setRefineText('');
  };

  // Helper to render text with interactive citation badges [1], [2], [3]
  const renderTextWithCitations = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const citationMatch = part.match(/^\[(\d+)\]$/);
      if (citationMatch) {
        const citeIndex = parseInt(citationMatch[1], 10);
        const isHighlighted = highlightedSourceIndex === citeIndex;

        return (
          <span
            key={i}
            onMouseEnter={() => setHighlightedSourceIndex(citeIndex)}
            onMouseLeave={() => setHighlightedSourceIndex(null)}
            className={`inline-flex items-center justify-center rounded px-1.5 py-0.5 mx-1 font-mono text-[12px] font-bold border transition-colors cursor-pointer ${
              isHighlighted
                ? 'bg-[#0F172A] text-white border-[#0F172A]'
                : 'bg-[#EFF6FF] text-[#0F172A] border-[#C6C6CD] hover:bg-[#D5E3FD]'
            }`}
            title={`Citation [${citeIndex}] - Hover to highlight source card`}
          >
            [{citeIndex}]
          </span>
        );
      }
      return <React.Fragment key={i}>{part}</React.Fragment>;
    });
  };

  return (
    <div className="flex-1 flex overflow-hidden relative bg-[#F7F9FB] h-full">
      {/* Main Chat Scroll Column */}
      <main className="flex-1 flex flex-col h-full overflow-y-auto relative min-w-0">
        <div className="flex-1 p-6 md:p-8 pb-36 max-w-[840px] w-full mx-auto space-y-12">
          {project.messages.map((msg) => {
            if (msg.role === 'user') {
              return (
                <div key={msg.id} className="flex flex-col gap-2">
                  <div className="flex items-center gap-2 text-[#45464D] text-[11px] font-bold uppercase tracking-wider">
                    <span className="material-symbols-outlined text-[16px]">person</span>
                    USER
                  </div>
                  <div className="text-[17px] leading-relaxed text-[#191C1E] font-medium bg-white p-4 rounded-lg border border-[#C6C6CD]/60 shadow-2xs">
                    {msg.content}
                  </div>
                </div>
              );
            }

            return (
              <div key={msg.id} className="flex flex-col gap-4 border-l-2 border-[#0F172A] pl-6">
                {/* Assistant Label */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[#0F172A] text-[11px] font-bold uppercase tracking-wider">
                    <span className="material-symbols-outlined text-[16px] fill-1">psychology</span>
                    RESEARCH ASSISTANT
                  </div>
                  <span className="text-[12px] text-[#76777D] font-mono">{msg.timestamp}</span>
                </div>

                {/* Synthesis Title */}
                {msg.title && (
                  <h2 className="text-[26px] md:text-[28px] font-bold text-[#0F172A] tracking-tight leading-snug mb-1">
                    {msg.title}
                  </h2>
                )}

                {/* Overview / Body Text */}
                <div className="text-[17px] leading-[26px] text-[#191C1E] mb-2 font-sans space-y-4">
                  <p>{renderTextWithCitations(msg.content)}</p>
                </div>

                {/* Sections */}
                {msg.sections?.map((sec, idx) => (
                  <div key={idx} className="space-y-3 mt-4">
                    <h3 className="text-[20px] font-bold text-[#0F172A] tracking-tight">
                      {sec.heading}
                    </h3>
                    <p className="text-[15px] leading-[24px] text-[#191C1E]">
                      {renderTextWithCitations(sec.body)}
                    </p>
                    {sec.bulletPoints && sec.bulletPoints.length > 0 && (
                      <ul className="list-disc pl-6 text-[15px] leading-[24px] text-[#191C1E] space-y-2 my-3">
                        {sec.bulletPoints.map((bp, bIdx) => (
                          <li key={bIdx}>{renderTextWithCitations(bp)}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}

                {/* Code / Formula Block */}
                {msg.codeSnippet && (
                  <div className="bg-[#1E293B] text-[#F8FAFC] p-4 rounded-md border border-slate-700 font-mono text-[13px] leading-relaxed overflow-x-auto my-4 shadow-sm relative group">
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        type="button"
                        onClick={() => navigator.clipboard.writeText(msg.codeSnippet!)}
                        className="bg-slate-700 text-xs px-2 py-1 rounded text-white hover:bg-slate-600"
                      >
                        Copy
                      </button>
                    </div>
                    <pre className="whitespace-pre">{msg.codeSnippet}</pre>
                  </div>
                )}
              </div>
            );
          })}

          {/* Loading Indicator */}
          {isSynthesizing && (
            <div className="flex items-center gap-3 border-l-2 border-[#0F172A] pl-6 py-4 animate-pulse">
              <span className="material-symbols-outlined text-[20px] text-[#0F172A] animate-spin">
                sync
              </span>
              <div className="text-[15px] text-[#45464D] font-medium">
                Synthesizing literature vectors & searching academic grounding databases...
              </div>
            </div>
          )}
        </div>

        {/* Refine Research Bottom Bar */}
        <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-[#F7F9FB]/95 backdrop-blur-xs border-t border-[#C6C6CD] flex justify-center z-10">
          <form
            onSubmit={handleRefineSubmit}
            className="max-w-[840px] w-full flex gap-3 items-center"
          >
            <input
              type="text"
              value={refineText}
              onChange={(e) => setRefineText(e.target.value)}
              disabled={isSynthesizing}
              placeholder="Refine research parameters or ask a follow-up question..."
              className="flex-1 bg-white border border-[#C6C6CD] rounded-md px-4 py-3.5 text-[15px] text-[#191C1E] focus:outline-none focus:border-[#0F172A] focus:ring-1 focus:ring-[#0F172A] transition-colors shadow-2xs placeholder:text-[#76777D]"
            />
            <button
              type="submit"
              disabled={!refineText.trim() || isSynthesizing}
              className={`px-6 py-3.5 rounded-md font-bold text-[12px] uppercase tracking-wider whitespace-nowrap flex items-center gap-2 transition-all cursor-pointer shadow-xs ${
                refineText.trim() && !isSynthesizing
                  ? 'bg-[#0F172A] text-white hover:bg-slate-800'
                  : 'bg-[#C6C6CD] text-white cursor-not-allowed'
              }`}
            >
              Refine Research
              <span className="material-symbols-outlined text-[18px]">send</span>
            </button>
          </form>
        </div>
      </main>

      {/* Right Sidebar (Sources Panel) */}
      <SourcesPanel
        sources={project.sources}
        highlightedSourceIndex={highlightedSourceIndex}
        onSourceHover={(idx) => setHighlightedSourceIndex(idx)}
        onViewBibliographyClick={onViewBibliographyClick}
      />
    </div>
  );
};
