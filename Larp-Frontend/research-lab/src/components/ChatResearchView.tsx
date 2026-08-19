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
            className={`inline-flex items-center justify-center rounded px-1.5 py-0.5 mx-1 font-mono text-[12px] font-bold border transition-colors cursor-pointer ${
              isHighlighted
                ? 'bg-[#0F172A] text-white border-[#0F172A]'
                : 'bg-[#EFF6FF] text-[#0F172A] border-[#C6C6CD] hover:bg-[#D5E3FD]'
            }`}
            title={`Citation [${citeIndex}] - Click to view source card`}
          >
            [{citeIndex}]
          </span>
        );
      }
      return <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer" {...props}>{children}</a>;
    },
    h1: ({ children }: any) => <h1 className="text-[26px] font-bold text-[#0F172A] mt-6 mb-4 leading-tight">{children}</h1>,
    h2: ({ children }: any) => <h2 className="text-[22px] font-bold text-[#0F172A] mt-6 mb-3 leading-tight">{children}</h2>,
    h3: ({ children }: any) => <h3 className="text-[18px] font-bold text-[#0F172A] mt-4 mb-2 leading-snug">{children}</h3>,
    p: ({ children }: any) => <p className="mb-4 text-[17px] leading-[26px] text-[#191C1E]">{children}</p>,
    ul: ({ children }: any) => <ul className="list-disc pl-6 mb-4 space-y-2 text-[17px] leading-[26px] text-[#191C1E]">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-[17px] leading-[26px] text-[#191C1E]">{children}</ol>,
    li: ({ children }: any) => <li>{children}</li>,
    strong: ({ children }: any) => <strong className="font-bold text-[#0F172A]">{children}</strong>,
    blockquote: ({ children }: any) => <blockquote className="border-l-4 border-[#C6C6CD] pl-4 italic text-[#45464D] my-4">{children}</blockquote>,
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
            className={`inline-flex items-center justify-center rounded px-1.5 py-0.5 mx-1 font-mono text-[12px] font-bold border transition-colors cursor-pointer ${
              isHighlighted
                ? 'bg-[#0F172A] text-white border-[#0F172A]'
                : 'bg-[#EFF6FF] text-[#0F172A] border-[#C6C6CD] hover:bg-[#D5E3FD]'
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
    <div className="flex-1 flex overflow-hidden relative bg-[#F7F9FB] h-full">
      {/* Main Chat Scroll Column */}
      <main className="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 md:p-8 max-w-[840px] w-full mx-auto space-y-8 pb-6">

          {/* ── Pipeline Progress Panel ─────────────────────────────── */}
          {showPipelinePanel && (
            <div className="bg-white border border-[#C6C6CD] rounded-lg shadow-xs overflow-hidden">
              {/* Header */}
              <button
                type="button"
                onClick={() => setIsPipelinePanelOpen((v) => !v)}
                className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-[#F7F9FB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[18px] text-[#0F172A]">account_tree</span>
                    <span className="font-bold text-[14px] text-[#0F172A] tracking-tight">Agent Pipeline</span>
                  </div>
                  {/* Step progress dots */}
                  <div className="flex items-center gap-1">
                    {displaySteps.map((step) => (
                      <span
                        key={step.id}
                        className={`w-2 h-2 rounded-full transition-all ${
                          step.status === 'done'    ? 'bg-emerald-500' :
                          step.status === 'running' ? 'bg-blue-500 animate-pulse' :
                          step.status === 'error'   ? 'bg-red-500' :
                                                      'bg-[#C6C6CD]'
                        }`}
                        title={step.name}
                      />
                    ))}
                  </div>
                  {isSynthesizing && (
                    <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                      Running
                    </span>
                  )}
                  {!isSynthesizing && displaySteps.length > 0 && (
                    <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                      Complete
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {/* Total cost badge */}
                  {parseFloat(totalCost) > 0 && (
                    <div className="flex items-center gap-1 text-[12px] font-mono font-bold text-[#45464D] bg-[#F2F4F6] border border-[#C6C6CD] px-2.5 py-1 rounded">
                      <span className="material-symbols-outlined text-[14px]">payments</span>
                      ${totalCost} USDC
                    </div>
                  )}
                  <span className={`material-symbols-outlined text-[18px] text-[#76777D] transition-transform ${
                    isPipelinePanelOpen ? 'rotate-180' : ''
                  }`}>expand_more</span>
                </div>
              </button>

              {/* Step rows (collapsible) */}
              {isPipelinePanelOpen && (
                <div className="border-t border-[#C6C6CD] divide-y divide-[#E0E3E5]">
                  {displaySteps.map((step, idx) => (
                    <div
                      key={step.id}
                      className={`flex items-center gap-4 px-5 py-3 transition-colors ${
                        step.status === 'running' ? 'bg-blue-50/60' : ''
                      }`}
                    >
                      {/* Step number */}
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[12px] font-bold border shrink-0 transition-colors ${
                        step.status === 'done'    ? 'bg-emerald-500 border-emerald-500 text-white' :
                        step.status === 'running' ? 'bg-blue-500 border-blue-500 text-white animate-pulse' :
                        step.status === 'error'   ? 'bg-red-500 border-red-500 text-white' :
                                                    'bg-white border-[#C6C6CD] text-[#76777D]'
                      }`}>
                        {step.status === 'done'    ? <span className="material-symbols-outlined text-[14px]">check</span> :
                         step.status === 'error'   ? <span className="material-symbols-outlined text-[14px]">close</span> :
                         step.status === 'running' ? <span className="material-symbols-outlined text-[14px] animate-spin" style={{ display: 'inline-block' }}>autorenew</span> :
                                                     String(idx + 1)}
                      </div>

                      {/* Step info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`font-bold text-[14px] ${
                            step.status === 'running' ? 'text-blue-700' :
                            step.status === 'done'    ? 'text-[#0F172A]' :
                            step.status === 'error'   ? 'text-red-600' :
                                                        'text-[#76777D]'
                          }`}>{step.name}</span>
                          <span className="text-[11px] text-[#76777D] bg-[#F2F4F6] border border-[#E0E3E5] px-1.5 py-0.5 rounded font-mono">
                            {step.api}
                          </span>
                        </div>
                        <p className="text-[12px] text-[#45464D] mt-0.5 truncate">{step.description}</p>
                        {step.error && (
                          <p className="text-[11px] text-red-500 mt-0.5">{step.error}</p>
                        )}
                      </div>

                      {/* Cost */}
                      {step.cost && (
                        <div className="shrink-0 text-right">
                          <div className="font-mono text-[12px] font-bold text-[#0F172A]">{step.cost}</div>
                          <div className="text-[10px] text-[#76777D] uppercase tracking-wider">paid (x402)</div>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Payment receipts summary */}
                  {displayPayments.length > 0 && (
                    <div className="px-5 py-3 bg-[#F7F9FB]">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="material-symbols-outlined text-[14px] text-[#45464D]">receipt_long</span>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[#45464D]">
                          x402 Payment Receipts ({displayPayments.length})
                        </span>
                      </div>
                      <div className="space-y-1 max-h-[120px] overflow-y-auto">
                        {displayPayments.map((p, i) => (
                          <div key={i} className="flex items-center justify-between text-[11px] font-mono">
                            <span className="text-[#45464D] truncate max-w-[200px]">{p.txHash.substring(0, 18)}...</span>
                            <span className="text-emerald-700 font-bold">{p.amount} USDC ✓</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

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
                <div className="font-sans">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={MarkdownComponents}
                  >
                    {preprocessMarkdown(msg.content)}
                  </ReactMarkdown>
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
            <div className="flex items-center gap-3 border-l-2 border-[#0F172A] pl-6 py-4">
              <span className="material-symbols-outlined text-[20px] text-[#0F172A] animate-spin" style={{ display: 'inline-block' }}>
                progress_activity
              </span>
              <div className="text-[15px] text-[#45464D] font-medium">
                Running 5-step research pipeline — searching, fact-checking, and synthesizing...
              </div>
            </div>
          )}
          </div>
        </div>

        {/* Refine Research Bottom Bar — pinned, never scrolls */}
        <div className="shrink-0 p-4 md:p-6 bg-[#F7F9FB]/95 backdrop-blur-sm border-t border-[#C6C6CD] flex justify-center z-10">
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

        {/* Mobile Floating Action Button for Sources Panel */}
        <button
          type="button"
          onClick={() => setIsSourcesMobileOpen(true)}
          className="md:hidden fixed bottom-20 right-4 z-30 bg-[#0F172A] text-white px-4 py-2.5 rounded-full shadow-lg border border-slate-700 font-bold text-[13px] flex items-center gap-2 hover:bg-slate-800 transition-transform active:scale-95 cursor-pointer"
          title="View Sources & Citations"
        >
          <span className="material-symbols-outlined text-[18px]">auto_stories</span>
          <span>Sources</span>
          {project.sources.length > 0 && (
            <span className="bg-white/20 px-2 py-0.5 rounded-full text-[11px] font-mono">
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
