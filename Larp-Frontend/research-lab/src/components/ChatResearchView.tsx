import React, { useState, useEffect, useRef } from 'react';
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [project.messages, isSynthesizing]);

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

  const preprocessMarkdown = (text: string) => {
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
            className={`inline-flex items-center justify-center rounded px-1.5 py-0.5 mx-1 font-mono text-[11px] font-bold border transition-colors cursor-pointer ${
              isHighlighted
                ? 'bg-[#10B981] text-[#09090B] border-[#10B981]'
                : 'bg-[#27272A] text-[#10B981] border-[#3F3F46] hover:bg-[#3F3F46]'
            }`}
            title={`Citation [${citeIndex}] - Click to view source card`}
          >
            [{citeIndex}]
          </span>
        );
      }
      return <a href={href} className="text-[#10B981] hover:underline" target="_blank" rel="noopener noreferrer" {...props}>{children}</a>;
    },
    h1: ({ children }: any) => <h1 className="text-[22px] font-bold text-[#F4F4F5] mt-6 mb-4 leading-tight">{children}</h1>,
    h2: ({ children }: any) => <h2 className="text-[18px] font-bold text-[#F4F4F5] mt-6 mb-3 leading-tight">{children}</h2>,
    h3: ({ children }: any) => <h3 className="text-[16px] font-bold text-[#F4F4F5] mt-4 mb-2 leading-snug">{children}</h3>,
    p: ({ children }: any) => <p className="mb-4 text-[15px] leading-[24px] text-[#D4D4D8]">{children}</p>,
    ul: ({ children }: any) => <ul className="list-disc pl-6 mb-4 space-y-2 text-[15px] leading-[24px] text-[#D4D4D8]">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-[15px] leading-[24px] text-[#D4D4D8]">{children}</ol>,
    li: ({ children }: any) => <li>{children}</li>,
    strong: ({ children }: any) => <strong className="font-bold text-[#F4F4F5]">{children}</strong>,
    blockquote: ({ children }: any) => <blockquote className="border-l-4 border-[#3F3F46] pl-4 italic text-[#A1A1AA] my-4">{children}</blockquote>,
  };

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
            className={`inline-flex items-center justify-center rounded px-1.5 py-0.5 mx-1 font-mono text-[11px] font-bold border transition-colors cursor-pointer ${
              isHighlighted
                ? 'bg-[#10B981] text-[#09090B] border-[#10B981]'
                : 'bg-[#27272A] text-[#10B981] border-[#3F3F46] hover:bg-[#3F3F46]'
            }`}
          >
            [{citeIndex}]
          </span>
        );
      }
      return <React.Fragment key={i}>{part}</React.Fragment>;
    });
  };

  return (
    <div className="flex-1 flex overflow-hidden relative bg-[#18181B] h-full text-[#F4F4F5]">
      {/* Main Chat Scroll Column */}
      <main className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative">
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 md:p-8 max-w-[760px] w-full mx-auto space-y-8 pb-[180px]">

          {/* Pipeline Progress Panel */}
          {showPipelinePanel && (
            <div className="bg-[#18181B] border border-[#27272A] rounded-xl overflow-hidden">
              <button
                type="button"
                onClick={() => setIsPipelinePanelOpen((v) => !v)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-[#27272A] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-[#A1A1AA]">account_tree</span>
                    <span className="font-medium text-[13px] text-[#D4D4D8]">Agent Pipeline</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {displaySteps.map((step) => (
                      <span
                        key={step.id}
                        className={`w-1.5 h-1.5 rounded-full transition-all ${
                          step.status === 'done'    ? 'bg-[#10B981]' :
                          step.status === 'running' ? 'bg-[#34D399] animate-pulse' :
                          step.status === 'error'   ? 'bg-red-500' :
                                                      'bg-[#3F3F46]'
                        }`}
                      />
                    ))}
                  </div>
                  {isSynthesizing && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#34D399] bg-[#10B981]/10 px-2 py-0.5 rounded">
                      Running
                    </span>
                  )}
                  {!isSynthesizing && displaySteps.length > 0 && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#A1A1AA] bg-[#27272A] px-2 py-0.5 rounded">
                      Complete
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {parseFloat(totalCost) > 0 && (
                    <div className="flex items-center gap-1 text-[11px] font-mono font-medium text-[#A1A1AA] bg-[#27272A] px-2 py-0.5 rounded">
                      <span className="material-symbols-outlined text-[14px]">payments</span>
                      ${totalCost} USDC
                    </div>
                  )}
                  <span className={`material-symbols-outlined text-[18px] text-[#76777D] transition-transform ${
                    isPipelinePanelOpen ? 'rotate-180' : ''
                  }`}>expand_more</span>
                </div>
              </button>

              {isPipelinePanelOpen && (
                <div className="border-t border-[#27272A] divide-y divide-[#27272A]">
                  {displaySteps.map((step, idx) => (
                    <div
                      key={step.id}
                      className="flex items-center gap-3 px-4 py-2"
                    >
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border shrink-0 ${
                        step.status === 'done'    ? 'bg-[#10B981]/10 border-[#10B981] text-[#10B981]' :
                        step.status === 'running' ? 'bg-[#34D399]/10 border-[#34D399] text-[#34D399] animate-pulse' :
                        step.status === 'error'   ? 'bg-red-500/10 border-red-500 text-red-500' :
                                                    'bg-[#18181B] border-[#3F3F46] text-[#A1A1AA]'
                      }`}>
                        {step.status === 'done'    ? <span className="material-symbols-outlined text-[12px]">check</span> :
                         step.status === 'error'   ? <span className="material-symbols-outlined text-[12px]">close</span> :
                         step.status === 'running' ? <span className="material-symbols-outlined text-[12px] animate-spin" style={{ display: 'inline-block' }}>autorenew</span> :
                                                     String(idx + 1)}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-[13px] text-[#D4D4D8]">{step.name}</span>
                          <span className="text-[10px] text-[#A1A1AA] bg-[#27272A] px-1.5 py-0.5 rounded font-mono">
                            {step.api}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#A1A1AA] truncate">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {project.messages.map((msg) => {
            if (msg.role === 'user') {
              return (
                <div key={msg.id} className="flex flex-col items-end gap-1 mb-6">
                  <div className="bg-[#27272A] text-[#F4F4F5] px-5 py-3 rounded-2xl rounded-tr-sm max-w-[85%] text-[15px] font-medium leading-relaxed">
                    {msg.content}
                  </div>
                </div>
              );
            }

            return (
              <div key={msg.id} className="flex flex-col gap-3 mb-8">
                <div className="flex items-center gap-2 text-[#A1A1AA] text-[11px] font-bold uppercase tracking-wider">
                  <span className="material-symbols-outlined text-[16px]">science</span>
                  Research Assistant
                </div>

                {msg.title && (
                  <h2 className="text-[20px] font-bold text-[#F4F4F5] tracking-tight leading-snug">
                    {msg.title}
                  </h2>
                )}

                <div className="font-sans text-[15px] leading-[24px]">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={MarkdownComponents}
                  >
                    {preprocessMarkdown(msg.content)}
                  </ReactMarkdown>
                </div>

                {msg.sections?.map((sec, idx) => (
                  <div key={idx} className="space-y-2 mt-4">
                    <h3 className="text-[16px] font-bold text-[#F4F4F5] tracking-tight">
                      {sec.heading}
                    </h3>
                    <p className="text-[15px] leading-[24px] text-[#D4D4D8]">
                      {renderTextWithCitations(sec.body)}
                    </p>
                    {sec.bulletPoints && sec.bulletPoints.length > 0 && (
                      <ul className="list-disc pl-6 text-[15px] leading-[24px] text-[#D4D4D8] space-y-1 my-2">
                        {sec.bulletPoints.map((bp, bIdx) => (
                          <li key={bIdx}>{renderTextWithCitations(bp)}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}

                {msg.codeSnippet && (
                  <div className="bg-[#09090B] border border-[#27272A] text-[#D4D4D8] p-4 rounded-xl font-mono text-[13px] leading-relaxed overflow-x-auto my-3 relative group">
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        type="button"
                        onClick={() => navigator.clipboard.writeText(msg.codeSnippet!)}
                        className="bg-[#27272A] text-[11px] px-2 py-1 rounded text-[#F4F4F5] hover:bg-[#3F3F46]"
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

          {isSynthesizing && (
            <div className="flex items-center gap-3 py-2 text-[#A1A1AA]">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-[#A1A1AA] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-[#A1A1AA] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-[#A1A1AA] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Floating Bottom Composer */}
        <div className="absolute bottom-0 left-0 right-0 p-6 flex justify-center bg-gradient-to-t from-[#18181B] via-[#18181B] to-transparent pointer-events-none">
          <form
            onSubmit={handleRefineSubmit}
            className="w-full max-w-[760px] bg-[#27272A] rounded-2xl border border-[#3F3F46] p-2 flex flex-col shadow-2xl pointer-events-auto transition-colors"
          >
            <textarea
              value={refineText}
              onChange={(e) => setRefineText(e.target.value)}
              disabled={isSynthesizing}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleRefineSubmit(e as any);
                }
              }}
              placeholder="Ask a follow-up question or refine parameters..."
              className="w-full bg-transparent border-none focus:outline-none focus:ring-0 resize-none min-h-[50px] max-h-[200px] p-2 text-[15px] text-[#F4F4F5] placeholder:text-[#A1A1AA] font-sans"
            />
            <div className="flex items-center justify-between px-2 pt-1">
              <div className="flex items-center gap-2 text-[12px] text-[#A1A1AA] font-medium">
                {project.attachedFiles.length > 0 && (
                  <span className="flex items-center gap-1 bg-[#18181B] px-2 py-1 rounded-md border border-[#3F3F46]">
                    <span className="material-symbols-outlined text-[14px]">attachment</span>
                    {project.attachedFiles.length} Attached
                  </span>
                )}
              </div>
              <button
                type="submit"
                disabled={!refineText.trim() || isSynthesizing}
                className={`p-2 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${
                  refineText.trim() && !isSynthesizing
                    ? 'bg-[#F4F4F5] text-[#18181B] hover:bg-[#D4D4D8]'
                    : 'bg-[#3F3F46] text-[#A1A1AA] cursor-not-allowed'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">arrow_upward</span>
              </button>
            </div>
          </form>
        </div>

        <button
          type="button"
          onClick={() => setIsSourcesMobileOpen(true)}
          className="md:hidden fixed bottom-28 right-4 z-30 bg-[#27272A] text-[#F4F4F5] px-4 py-2.5 rounded-full shadow-lg border border-[#3F3F46] font-bold text-[13px] flex items-center gap-2 hover:bg-[#3F3F46] transition-transform active:scale-95 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">auto_stories</span>
          <span>Sources</span>
        </button>
      </main>

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
