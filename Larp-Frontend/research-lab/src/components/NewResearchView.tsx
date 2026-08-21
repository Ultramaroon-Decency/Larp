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
    <div className="flex-1 flex flex-col items-center justify-center p-6 md:p-8 overflow-y-auto bg-[#18181B] relative">
      <div className="w-full max-w-[760px] flex flex-col gap-12 my-auto pb-[180px]">
        {/* Headline */}
        <div className="text-center space-y-3">
          <h2 className="text-[32px] md:text-[36px] font-bold text-[#F4F4F5] tracking-tight leading-tight">
            What would you like to research?
          </h2>
          <p className="text-[16px] md:text-[17px] text-[#A1A1AA] max-w-2xl mx-auto font-medium">
            Search literature, analyze sources, and synthesize complex questions.
          </p>
        </div>

        {/* Suggested Prompts */}
        <div className="flex flex-wrap justify-center gap-2 max-w-[640px] mx-auto">
          {SUGGESTED_VECTORS.map((vector) => (
            <button
              key={vector.id}
              type="button"
              onClick={() => handleSelectSuggested(vector.query)}
              className="px-4 py-2 rounded-full border border-[#3F3F46] bg-[#27272A] hover:bg-[#3F3F46] hover:border-[#52525B] text-[#D4D4D8] transition-colors cursor-pointer text-[13px] font-medium"
            >
              {vector.title}
            </button>
          ))}
        </div>
      </div>

      {/* Floating Bottom Composer */}
      <div className="absolute bottom-0 left-0 right-0 p-6 flex justify-center bg-gradient-to-t from-[#18181B] via-[#18181B] to-transparent pointer-events-none">
        <form
          onSubmit={handleSubmit}
          onDragOver={(e) => {
            e.preventDefault();
            setIsHoveringDropzone(true);
          }}
          onDragLeave={() => setIsHoveringDropzone(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsHoveringDropzone(false);
            if (e.dataTransfer.files) {
              handleFileUpload(e.dataTransfer.files);
            }
          }}
          className={`w-full max-w-[760px] bg-[#27272A] rounded-2xl border ${
            isHoveringDropzone ? 'border-[#10B981] bg-[#27272A]/80' : 'border-[#3F3F46]'
          } p-3 flex flex-col shadow-2xl pointer-events-auto transition-colors`}
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
            placeholder="Ask a research question..."
            className="w-full bg-transparent border-none focus:outline-none focus:ring-0 resize-none min-h-[96px] p-2 text-[16px] text-[#F4F4F5] placeholder:text-[#A1A1AA] font-sans"
          />

          {/* Attached Files */}
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 px-2 pb-2">
              {attachedFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-1.5 bg-[#18181B] text-[#F4F4F5] border border-[#3F3F46] px-2.5 py-1 rounded-lg text-[12px] font-medium"
                >
                  <span className="material-symbols-outlined text-[14px] text-[#10B981]">description</span>
                  <span className="truncate max-w-[150px]">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(file.id)}
                    className="hover:text-red-400 ml-1 text-[14px]"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-2 px-2 pt-2 border-t border-[#3F3F46]">
            <div className="flex flex-wrap items-center gap-2">
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
                className="flex items-center gap-1.5 px-3 py-1.5 text-[#A1A1AA] hover:text-[#F4F4F5] hover:bg-[#3F3F46] rounded-lg transition-colors text-[13px] font-medium cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">add_circle</span>
                Attach
              </button>

              <div className="h-4 w-px bg-[#3F3F46] mx-1"></div>

              <div className="relative group">
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value as ResearchMode)}
                  className="appearance-none bg-transparent text-[#A1A1AA] hover:text-[#F4F4F5] px-3 py-1.5 pr-8 rounded-lg transition-colors hover:bg-[#3F3F46] cursor-pointer text-[13px] font-medium outline-none"
                >
                  <option value="quick" className="bg-[#27272A]">Quick Scan</option>
                  <option value="deep" className="bg-[#27272A]">Deep Dive</option>
                </select>
                <span className="material-symbols-outlined text-[16px] absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-[#A1A1AA] group-hover:text-[#F4F4F5]">
                  arrow_drop_down
                </span>
              </div>
            </div>

            <button
              type="submit"
              disabled={!query.trim()}
              className={`p-2 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${
                query.trim()
                  ? 'bg-[#F4F4F5] text-[#18181B] hover:bg-[#D4D4D8]'
                  : 'bg-[#3F3F46] text-[#A1A1AA] cursor-not-allowed'
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">arrow_upward</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
