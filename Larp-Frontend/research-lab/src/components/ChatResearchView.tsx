// src/components/ChatResearchView.tsx
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ResearchProject, PipelineStep, PaymentReceipt } from '../types';
import { SourcesPanel } from './SourcesPanel';

interface ChatResearchViewProps {
  project: ResearchProject;
  onRefineQuery: (refineText: string) => void;
  onViewBibliographyClick: () => void;
  isSynthesizing: boolean;
  livePipelineSteps: PipelineStep[];
  livePayments: PaymentReceipt[];
}

export const ChatResearchView: React.FC<ChatResearchViewProps> = ({
  project,
  onRefineQuery,
  onViewBibliographyClick,
  isSynthesizing,
  livePipelineSteps,
  livePayments,
}) => {
  const [refineText, setRefineText] = useState('');
  const [highlightedSourceIndex, setHighlightedSourceIndex] = useState<number | null>(null);
  const [isPipelinePanelOpen, setIsPipelinePanelOpen] = useState(true);
  const [isSourcesMobileOpen, setIsSourcesMobileOpen] = useState(false);

  // Use live steps during synthesis, fall back to project's stored steps after
  const displaySteps: PipelineStep[] =
    livePipelineSteps.length > 0
      ? livePipelineSteps
      : (project.pipelineSteps ?? []);

  const displayPayments: PaymentReceipt[] =
    livePayments.length > 0
      ? livePayments
      : (project.payments ?? []);

  const totalCost = displayPayments
    .reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0)
    .toFixed(4);

  const showPipelinePanel = displaySteps.length > 0;

  const handleRefineSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!refineText.trim() || isSynthesizing) return;
    onRefineQuery(refineText);
    setRefineText('');
  };

  const handleCitationClick = (citeIndex: number) => {
    setHighlightedSourceIndex(citeIndex);
    setIsSourcesMobileOpen(true);
  };

  // Helper to process markdown text before rendering
  const preprocessMarkdown = (text: string) => {
    // Replace [1] with a markdown link to cite:1, ignoring those already in links or preceded by "Source "
    return text.replace(/(?<!\[Source\s*)\[(\d+)\](?!\()/g, '[$1](cite:$1)');
  };

  const MarkdownComponents = {
    a: ({ href, children, ...props }: any) => {
      if (href?.startsWith('cite:')) {
        const citeIndex = parseInt(href.replace('cite:', ''), 10);
        const isHighlighted = highlightedSourceIndex === citeIndex;
        return (
          <span
            onClick={() => handleCitationClick(citeIndex)}
            onMouseEnter={() => setHighlightedSourceIndex(citeIndex)}
            onMouseLeave={() => setHighlightedSourceIndex(null)}
            className={`inline-flex items-center justify-center rounded px-1.5 py-0.5 mx-1 font-mono text-[11px] font-bold border transition-colors cursor-pointer outline-none ${
              isHighlighted
                ? 'bg-primary text-white border-primary'
                : 'bg-[#131E35] text-primary border-primary/20 hover:bg-[#1A263E]'
            }`}
            title={`Citation [${citeIndex}] - Click to view source card`}
          >
            [{citeIndex}]
          </span>
        );
      }
      return <a href={href} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer" {...props}>{children}</a>;
    },
    h1: ({ children }: any) => <h1 className="text-[24px] font-bold text-white mt-6 mb-3 leading-tight font-sans">{children}</h1>,
    h2: ({ children }: any) => <h2 className="text-[20px] font-bold text-white mt-5 mb-2.5 leading-tight font-sans">{children}</h2>,
    h3: ({ children }: any) => <h3 className="text-[17px] font-semibold text-zinc-200 mt-4 mb-2 leading-snug font-sans">{children}</h3>,
    p: ({ children }: any) => <p className="mb-4 text-[15px] leading-[24px] text-zinc-300 font-sans">{children}</p>,
    ul: ({ children }: any) => <ul className="list-disc pl-6 mb-4 space-y-2 text-[15px] leading-[24px] text-zinc-300 font-sans">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-[15px] leading-[24px] text-zinc-300 font-sans">{children}</ol>,
    li: ({ children }: any) => <li className="pl-0.5">{children}</li>,
    strong: ({ children }: any) => <strong className="font-semibold text-white">{children}</strong>,
    blockquote: ({ children }: any) => <blockquote className="border-l-2 border-primary/40 pl-4 italic text-zinc-400 my-4 bg-zinc-900/20 py-0.5">{children}</blockquote>,
  };

  // Keep this for the older sections rendering
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
            onClick={() => handleCitationClick(citeIndex)}
            onMouseEnter={() => setHighlightedSourceIndex(citeIndex)}
            onMouseLeave={() => setHighlightedSourceIndex(null)}
            className={`inline-flex items-center justify-center rounded px-1.5 py-0.5 mx-1 font-mono text-[11px] font-bold border transition-colors cursor-pointer outline-none ${
              isHighlighted
                ? 'bg-primary text-white border-primary'
                : 'bg-[#131E35] text-primary border-primary/20 hover:bg-[#1A263E]'
            }`}
            title={`Citation [${citeIndex}] - Click to view source card`}
          >
            [{citeIndex}]
          </span>
        );
      }
      return <React.Fragment key={i}>{part}</React.Fragment>;
    });
  };

  return (
    <div className="flex-1 flex overflow-hidden relative bg-[#090D16] h-full text-[#E5E7EB]">
      {/* Main Chat Scroll Column */}
      <main className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative">
        <div className="flex-1 overflow-y-auto pb-[130px]">
          <div className="p-4 md:p-8 max-w-[760px] w-full mx-auto space-y-10">

            {/* ── Collapsible Pipeline Progress Panel ─────────────────────────────── */}
            {showPipelinePanel && (
              <div className="bg-[#0D1525] border border-[#1B2536] rounded-xl overflow-hidden shadow-md">
                {/* Header */}
                <button
                  type="button"
                  onClick={() => setIsPipelinePanelOpen((v) => !v)}
                  className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-[#131E31]/40 transition-colors outline-none cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[18px] text-primary">account_tree</span>
                      <span className="font-bold text-[13px] text-white tracking-tight">Agent Pipeline</span>
                    </div>
                    {/* Step progress dots */}
                    <div className="flex items-center gap-1">
                      {displaySteps.map((step) => (
                        <span
                          key={step.id}
                          className={`w-1.5 h-1.5 rounded-full transition-all ${
                            step.status === 'done'    ? 'bg-emerald-500 shadow-xs' :
                            step.status === 'running' ? 'bg-blue-500 animate-pulse shadow-md' :
                            step.status === 'error'   ? 'bg-red-500' :
                                                        'bg-zinc-700'
                          }`}
                          title={step.name}
                        />
                      ))}
                    </div>
                    {isSynthesizing && (
                      <span className="text-[9px] font-bold uppercase tracking-wider text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-md">
                        Running
                      </span>
                    )}
                    {!isSynthesizing && displaySteps.length > 0 && (
                      <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md">
                        Complete
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {/* Total cost badge */}
                    {parseFloat(totalCost) > 0 && (
                      <div className="flex items-center gap-1 text-[11px] font-mono font-bold text-zinc-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded">
                        <span className="material-symbols-outlined text-[13px]">payments</span>
                        ${totalCost} USDC
                      </div>
                    )}
                    <span className={`material-symbols-outlined text-[18px] text-zinc-500 transition-transform ${
                      isPipelinePanelOpen ? 'rotate-180' : ''
                    }`}>expand_more</span>
                  </div>
                </button>

                {/* Step rows (collapsible) */}
                {isPipelinePanelOpen && (
                  <div className="border-t border-[#1B2536] divide-y divide-zinc-900 bg-black/10">
                    {displaySteps.map((step, idx) => (
                      <div
                        key={step.id}
                        className={`flex items-center gap-4 px-5 py-3 transition-colors ${
                          step.status === 'running' ? 'bg-primary/5' : ''
                        }`}
                      >
                        {/* Step number */}
                        <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border shrink-0 transition-colors ${
                          step.status === 'done'    ? 'bg-emerald-500 border-emerald-500 text-white' :
                          step.status === 'running' ? 'bg-primary border-primary text-white animate-pulse' :
                          step.status === 'error'   ? 'bg-red-500 border-red-500 text-white' :
                                                      'bg-transparent border-zinc-700 text-zinc-500'
                        }`}>
                          {step.status === 'done'    ? <span className="material-symbols-outlined text-[12px]">check</span> :
                           step.status === 'error'   ? <span className="material-symbols-outlined text-[12px]">close</span> :
                           step.status === 'running' ? <span className="material-symbols-outlined text-[12px] animate-spin">sync</span> :
                                                       String(idx + 1)}
                        </div>

                        {/* Step info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`font-semibold text-[13px] ${
                              step.status === 'running' ? 'text-primary' :
                              step.status === 'done'    ? 'text-white' :
                              step.status === 'error'   ? 'text-red-500' :
                                                          'text-zinc-500'
                            }`}>{step.name}</span>
                            <span className="text-[9px] text-zinc-500 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded font-mono">
                              {step.api}
                            </span>
                          </div>
                          <p className="text-[11px] text-zinc-400 mt-0.5 truncate">{step.description}</p>
                          {step.error && (
                            <p className="text-[10px] text-red-400 mt-0.5">{step.error}</p>
                          )}
                        </div>

                        {/* Cost */}
                        {step.cost && (
                          <div className="shrink-0 text-right">
                            <div className="font-mono text-[11px] font-bold text-white">{step.cost}</div>
                            <div className="text-[9px] text-zinc-500 uppercase tracking-wider font-semibold">ASA</div>
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Payment receipts summary */}
                    {displayPayments.length > 0 && (
                      <div className="px-5 py-3 border-t border-[#1B2536] bg-black/20">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="material-symbols-outlined text-[14px] text-zinc-500">receipt_long</span>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                            Payment Log Receipts ({displayPayments.length})
                          </span>
                        </div>
                        <div className="space-y-1 max-h-[110px] overflow-y-auto">
                          {displayPayments.map((p, i) => (
                            <div key={i} className="flex items-center justify-between text-[10px] font-mono">
                              <span className="text-zinc-500 truncate max-w-[200px]">{p.txHash}</span>
                              <span className="text-emerald-500 font-semibold">{p.amount} USDC ✓</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Conversation Flow Feed */}
            {project.messages.map((msg) => {
              if (msg.role === 'user') {
                return (
                  <div key={msg.id} className="flex flex-col items-end gap-1.5">
                    <span className="text-[9px] font-bold text-zinc-500 tracking-wider uppercase pr-2">You</span>
                    <div className="text-[15px] leading-relaxed text-white font-medium bg-[#131E35] border border-[#1F2E49] px-4 py-3 rounded-2xl max-w-[85%] shadow-xs">
                      {msg.content}
                    </div>
                  </div>
                );
              }

              return (
                <div key={msg.id} className="flex gap-4 items-start pl-1">
                  {/* Modern AI Icon */}
                  <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 mt-1">
                    <span className="material-symbols-outlined text-[18px]">psychology</span>
                  </div>

                  <div className="flex-1 min-w-0 space-y-4">
                    {/* Header bar */}
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-bold text-zinc-400 tracking-wider uppercase">Assistant</span>
                      <span className="text-[10px] text-zinc-500 font-mono">{msg.timestamp}</span>
                    </div>

                    {/* Synthesis Title */}
                    {msg.title && (
                      <h2 className="text-[22px] md:text-[24px] font-bold text-white tracking-tight leading-snug mb-1">
                        {msg.title}
                      </h2>
                    )}

                    {/* Body content via Markdown */}
                    <div className="font-sans leading-relaxed text-zinc-300">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={MarkdownComponents}
                      >
                        {preprocessMarkdown(msg.content)}
                      </ReactMarkdown>
                    </div>

                    {/* Supporting Sections */}
                    {msg.sections?.map((sec, idx) => (
                      <div key={idx} className="space-y-2 mt-4 bg-zinc-950/20 p-4 rounded-xl border border-zinc-900/40">
                        <h3 className="text-[17px] font-bold text-white tracking-tight">
                          {sec.heading}
                        </h3>
                        <p className="text-[14px] leading-[22px] text-zinc-300">
                          {renderTextWithCitations(sec.body)}
                        </p>
                        {sec.bulletPoints && sec.bulletPoints.length > 0 && (
                          <ul className="list-disc pl-5 text-[14px] leading-[22px] text-zinc-300 space-y-1.5 my-2">
                            {sec.bulletPoints.map((bp, bIdx) => (
                              <li key={bIdx}>{renderTextWithCitations(bp)}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}

                    {/* Code / Formula Block */}
                    {msg.codeSnippet && (
                      <div className="bg-[#0C1220] text-zinc-300 p-4 rounded-xl border border-[#1B2536] font-mono text-[12px] leading-relaxed overflow-x-auto my-4 shadow-md relative group">
                        <button
                          type="button"
                          onClick={() => navigator.clipboard.writeText(msg.codeSnippet!)}
                          className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity bg-zinc-900 border border-zinc-800 text-[10px] px-2.5 py-1 rounded-md text-white hover:bg-zinc-800 cursor-pointer outline-none font-sans"
                        >
                          Copy
                        </button>
                        <pre className="whitespace-pre">{msg.codeSnippet}</pre>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Loading Indicator */}
            {isSynthesizing && (
              <div className="flex gap-4 items-start pl-1 py-2">
                <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 animate-pulse">
                  <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                </div>
                <div className="flex-1">
                  <span className="text-[9px] font-bold text-zinc-500 tracking-wider uppercase block mb-1">Synthesizing</span>
                  <div className="text-[14px] text-zinc-400 font-medium animate-pulse">
                    Running 5-step research pipeline — querying nodes, validating, and writing synthesis...
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>

        {/* Floating Bottom Composer Bar */}
        <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-[#090D16] via-[#090D16]/95 to-transparent z-10">
          <form
            onSubmit={handleRefineSubmit}
            className="max-w-[760px] w-full mx-auto flex gap-2 items-center bg-[#0D1525] border border-[#1F2E49] rounded-xl p-1.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all shadow-xl"
          >
            <input
              type="text"
              value={refineText}
              onChange={(e) => setRefineText(e.target.value)}
              disabled={isSynthesizing}
              placeholder="Refine research parameters or ask follow-up questions..."
              className="flex-1 bg-transparent border-none px-3.5 py-2.5 text-[14px] text-white focus:outline-none focus:ring-0 placeholder-zinc-500"
            />
            <button
              type="submit"
              disabled={!refineText.trim() || isSynthesizing}
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-all cursor-pointer outline-none shrink-0 ${
                refineText.trim() && !isSynthesizing
                  ? 'bg-primary text-white hover:bg-blue-600'
                  : 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">send</span>
            </button>
          </form>
        </div>

        {/* Mobile Floating Action Button for Sources Panel */}
        <button
          type="button"
          onClick={() => setIsSourcesMobileOpen(true)}
          className="md:hidden fixed bottom-24 right-4 z-30 bg-primary text-white px-4 py-2 rounded-full shadow-lg border border-primary/20 font-bold text-[12px] flex items-center gap-2 hover:bg-blue-600 transition-transform active:scale-95 cursor-pointer outline-none"
          title="View Sources"
        >
          <span className="material-symbols-outlined text-[16px]">auto_stories</span>
          <span>Sources</span>
          {project.sources.length > 0 && (
            <span className="bg-white/20 px-2 py-0.5 rounded-full text-[10px] font-mono">
              {project.sources.length}
            </span>
          )}
        </button>
      </main>

      {/* Right Sidebar (Sources Panel) */}
      <SourcesPanel
        sources={project.sources}
        highlightedSourceIndex={highlightedSourceIndex}
        onSourceHover={(idx) => setHighlightedSourceIndex(idx)}
        onViewBibliographyClick={onViewBibliographyClick}
        isOpenMobile={isSourcesMobileOpen}
        onCloseMobile={() => setIsSourcesMobileOpen(false)}
      />
    </div>
  );
};
