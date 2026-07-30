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
    <div className="flex-1 flex flex-col items-center justify-center p-6 md:p-8 overflow-y-auto">
      <div className="w-full max-w-[840px] flex flex-col gap-8 my-auto">
        {/* Headline */}
        <div className="text-center space-y-2">
          <h2 className="text-[32px] md:text-[36px] font-bold text-[#0F172A] tracking-tight leading-tight">
            Initiate Research Protocol
          </h2>
          <p className="text-[16px] md:text-[17px] text-[#45464D] max-w-2xl mx-auto">
            Define your parameters, input queries, or upload source material to begin synthesis.
          </p>
        </div>

        {/* Primary Input Card */}
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-lg border border-[#C6C6CD] p-3 flex flex-col focus-within:border-[#0F172A] focus-within:ring-1 focus-within:ring-[#0F172A] transition-all shadow-xs"
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
            placeholder="State your research objective, thesis question, or technical query here..."
            className="w-full bg-transparent border-none focus:outline-none focus:ring-0 resize-none min-h-[130px] p-3 text-[16px] text-[#191C1E] placeholder:text-[#76777D] font-sans"
          />

          {/* Attached Files List Pill Chips */}
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 p-2 border-t border-[#C6C6CD]/40">
              {attachedFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-1.5 bg-[#F2F4F6] text-[#0F172A] border border-[#C6C6CD] px-2.5 py-1 rounded-md text-[12px] font-medium"
                >
                  <span className="material-symbols-outlined text-[14px]">description</span>
                  <span className="truncate max-w-[180px]">{file.name}</span>
                  <span className="text-[#45464D] text-[10px]">({file.size})</span>
                  <button
                    type="button"
                    onClick={() => removeFile(file.id)}
                    className="hover:text-red-600 ml-1 text-[14px]"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-2 border-t border-[#C6C6CD]/40 mt-1">
            <div className="flex flex-wrap items-center gap-2">
              {/* Research Mode Selection Toggle */}
              <div className="flex items-center bg-[#F2F4F6] rounded-md p-1 border border-[#C6C6CD]">
                <button
                  type="button"
                  onClick={() => setMode('quick')}
                  className={`px-3 py-1.5 rounded-md text-[11px] font-bold tracking-wider uppercase flex items-center gap-1.5 transition-all cursor-pointer ${
                    mode === 'quick'
                      ? 'bg-white border border-[#C6C6CD] shadow-xs text-[#0F172A]'
                      : 'text-[#45464D] hover:text-[#0F172A]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[14px]">speed</span>
                  Quick Scan
                </button>

                <button
                  type="button"
                  onClick={() => setMode('deep')}
                  className={`px-3 py-1.5 rounded-md text-[11px] font-bold tracking-wider uppercase flex items-center gap-1.5 transition-all cursor-pointer ${
                    mode === 'deep'
                      ? 'bg-white border border-[#C6C6CD] shadow-xs text-[#0F172A]'
                      : 'text-[#45464D] hover:text-[#0F172A]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[14px]">plumbing</span>
                  Deep Dive
                </button>
              </div>

              {/* Attach References Button */}
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
                className="flex items-center gap-1.5 px-3 py-2 text-[#45464D] hover:text-[#0F172A] hover:bg-[#E0E3E5] rounded-md transition-colors text-[13px] font-medium cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">upload_file</span>
                Attach References
              </button>
            </div>

            {/* Submit Action Button */}
            <button
              type="submit"
              disabled={!query.trim()}
              className={`px-6 py-2.5 rounded-md font-bold text-[12px] tracking-wider uppercase flex items-center gap-2 transition-all cursor-pointer shadow-xs ${
                query.trim()
                  ? 'bg-[#0F172A] text-white hover:bg-slate-800'
                  : 'bg-[#C6C6CD] text-white cursor-not-allowed'
              }`}
            >
              Synthesize
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </form>

        {/* Suggested Vectors Section */}
        <div>
          <h3 className="text-[11px] font-bold tracking-wider text-[#45464D] uppercase mb-4">
            Suggested Vectors
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {SUGGESTED_VECTORS.map((vector) => (
              <button
                key={vector.id}
                type="button"
                onClick={() => handleSelectSuggested(vector.query)}
                className="text-left p-4 rounded-md bg-white border border-[#C6C6CD] hover:border-[#0F172A] hover:bg-[#F8FAFC] transition-all group cursor-pointer"
              >
                <div className="flex items-start gap-3">
                  <div className="bg-[#D5E3FD] text-[#0D1C2F] p-2 rounded-md shrink-0">
                    <span className="material-symbols-outlined text-[20px]">{vector.icon}</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-[15px] text-[#0F172A] group-hover:text-[#2563EB] transition-colors leading-snug">
                      {vector.title}
                    </h4>
                    <p className="text-[13px] text-[#45464D] mt-1 line-clamp-2 leading-relaxed">
                      {vector.description}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Drag and Drop Zone */}
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
          className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center transition-colors cursor-pointer ${
            isHoveringDropzone
              ? 'border-[#0F172A] bg-[#E0E3E5]'
              : 'border-[#C6C6CD] bg-[#F2F4F6] hover:bg-[#E0E3E5]/70'
          }`}
        >
          <div className="bg-white p-3 rounded-full shadow-xs border border-[#C6C6CD] mb-3">
            <span className="material-symbols-outlined text-[24px] text-[#0F172A]">
              folder_open
            </span>
          </div>
          <h4 className="font-bold text-[18px] text-[#0F172A] mb-1">
            Upload Source Material
          </h4>
          <p className="text-[13px] text-[#45464D] max-w-md leading-relaxed">
            Drag and drop PDFs, datasets (CSV/JSON), or text files to establish a localized knowledge base for this session.
          </p>
        </div>
      </div>
    </div>
  );
};
