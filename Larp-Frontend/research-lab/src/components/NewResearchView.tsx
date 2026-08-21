// src/components/NewResearchView.tsx
import React, { useState, useRef } from 'react';
import { ResearchMode, AttachedFile } from '../types';
import { SUGGESTED_VECTORS } from '../data/mockData';

interface NewResearchViewProps {
  onSynthesize: (query: string, mode: ResearchMode, attachedFiles: AttachedFile[]) => void;
}

export const NewResearchView: React.FC<NewResearchViewProps> = ({ onSynthesize }) => {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<ResearchMode>('quick');
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isHoveringDropzone, setIsHoveringDropzone] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    onSynthesize(query, mode, attachedFiles);
  };

  const handleSelectSuggested = (suggestedQuery: string) => {
    setQuery(suggestedQuery);
  };

  const handleFileUpload = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const newFiles: AttachedFile[] = Array.from(files).map((file, idx) => ({
      id: `file-${Date.now()}-${idx}`,
      name: file.name,
      size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      type: file.type || 'document'
    }));
    setAttachedFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (id: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-start p-6 md:p-12 overflow-y-auto bg-[#090D16] text-[#E5E7EB]">
      <div className="w-full max-w-[720px] flex flex-col gap-10 my-auto py-10">
        {/* Modern AI Assistant Welcome Header */}
        <div className="text-center space-y-3">
          <h2 className="text-[32px] md:text-[38px] font-bold text-white tracking-tight leading-tight font-sans">
            What would you like to research?
          </h2>
          <p className="text-[14px] md:text-[15px] text-[#9CA3AF] max-w-lg mx-auto font-sans leading-relaxed">
            Search scientific literature, analyze complex datasets, and run multi-step agent syntheses with ease.
          </p>
        </div>

        {/* Premium Floating Composer */}
        <form
          onSubmit={handleSubmit}
          className="bg-[#0D1525] rounded-xl border border-[#1F2E49] p-2 flex flex-col focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all shadow-xl"
        >
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="Ask a research question or define a thesis parameter..."
            className="w-full bg-transparent border-none focus:outline-none focus:ring-0 resize-none min-h-[110px] p-3 text-[15px] text-white placeholder-zinc-500 font-sans leading-relaxed"
          />

          {/* Attached Files chip list inside composer */}
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 p-2 border-t border-[#1F2E49]/50">
              {attachedFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-1.5 bg-[#172237] text-white border border-[#253550] px-2.5 py-1 rounded-lg text-[11px] font-medium"
                >
                  <span className="material-symbols-outlined text-[13px] text-primary">description</span>
                  <span className="truncate max-w-[150px]">{file.name}</span>
                  <span className="text-zinc-500 text-[9px]">({file.size})</span>
                  <button
                    type="button"
                    onClick={() => removeFile(file.id)}
                    className="hover:text-red-400 ml-1 text-[13px] font-bold outline-none"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Composer Controls Bar */}
          <div className="flex items-center justify-between gap-3 p-1.5 border-t border-[#1F2E49]/30 mt-1">
            <div className="flex items-center gap-2">
              {/* Clean Research Mode Toggle */}
              <div className="flex items-center bg-[#070B13] rounded-lg p-0.5 border border-[#1F2E49]">
                <button
                  type="button"
                  onClick={() => setMode('quick')}
                  className={`px-3 py-1.5 rounded-md text-[10px] font-bold tracking-wider uppercase flex items-center gap-1.5 transition-all cursor-pointer outline-none ${
                    mode === 'quick'
                      ? 'bg-[#172237] text-white shadow-xs'
                      : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  <span className="material-symbols-outlined text-[13px]">speed</span>
                  Quick Scan
                </button>

                <button
                  type="button"
                  onClick={() => setMode('deep')}
                  className={`px-3 py-1.5 rounded-md text-[10px] font-bold tracking-wider uppercase flex items-center gap-1.5 transition-all cursor-pointer outline-none ${
                    mode === 'deep'
                      ? 'bg-[#172237] text-white shadow-xs'
                      : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  <span className="material-symbols-outlined text-[13px]">plumbing</span>
                  Deep Dive
                </button>
              </div>

              {/* Attach File Button */}
              <input
                type="file"
                ref={fileInputRef}
                onChange={(e) => handleFileUpload(e.target.files)}
                multiple
                className="hidden"
                accept=".pdf,.csv,.json,.txt,.doc,.docx"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 px-3 py-2 text-zinc-400 hover:text-white hover:bg-[#172237] rounded-lg transition-colors text-[12px] font-medium cursor-pointer outline-none"
              >
                <span className="material-symbols-outlined text-[16px]">upload_file</span>
                Attach References
              </button>
            </div>

            {/* Submit Action Button (Circular Up Arrow) */}
            <button
              type="submit"
              disabled={!query.trim()}
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-all cursor-pointer shadow-md shrink-0 outline-none ${
                query.trim()
                  ? 'bg-primary text-white hover:bg-blue-600 scale-100'
                  : 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
              }`}
            >
              <span className="material-symbols-outlined text-[18px] font-bold">arrow_upward</span>
            </button>
          </div>
        </form>

        {/* Suggested Prompt Chips */}
        <div className="space-y-3">
          <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-500 block">Suggested Prompts</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {SUGGESTED_VECTORS.map((vector) => (
              <button
                key={vector.id}
                type="button"
                onClick={() => handleSelectSuggested(vector.query)}
                className="text-left p-3.5 rounded-xl bg-[#0D1525] border border-[#1B2536] hover:border-primary/50 hover:bg-[#131E35] transition-all group cursor-pointer outline-none flex gap-3"
              >
                <div className="bg-[#172237] text-primary p-2 rounded-lg shrink-0 flex items-center justify-center h-8 w-8">
                  <span className="material-symbols-outlined text-[16px]">{vector.icon}</span>
                </div>
                <div className="min-w-0">
                  <h4 className="font-semibold text-[13px] text-white group-hover:text-primary transition-colors truncate">
                    {vector.title}
                  </h4>
                  <p className="text-[11px] text-[#9CA3AF] mt-0.5 line-clamp-1">
                    {vector.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Quiet Drag and Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsHoveringDropzone(true);
          }}
          onDragLeave={() => setIsHoveringDropzone(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsHoveringDropzone(false);
            handleFileUpload(e.dataTransfer.files);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`border border-dashed rounded-xl p-6 flex flex-col items-center justify-center text-center transition-all cursor-pointer ${
            isHoveringDropzone
              ? 'border-primary bg-[#131E35]'
              : 'border-[#1F2E49] bg-[#070B13] hover:bg-[#0D1525]'
          }`}
        >
          <span className="material-symbols-outlined text-[20px] text-primary mb-2">cloud_upload</span>
          <h4 className="font-semibold text-[13px] text-white mb-0.5">Upload Source Materials</h4>
          <p className="text-[11px] text-zinc-500 max-w-sm">
            Drag and drop research PDFs, CSV datasets, or reference docs to use local source context.
          </p>
        </div>
      </div>
    </div>
  );
};
