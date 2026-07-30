import React from 'react';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const UpgradeModal: React.FC<UpgradeModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative bg-white rounded-xl border border-[#C6C6CD] shadow-2xl max-w-lg w-full p-6 z-10 space-y-6">
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-full bg-[#0F172A] text-white flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px]">bolt</span>
            </div>
            <div>
              <h3 className="text-[20px] font-bold text-[#0F172A]">Upgrade Plan</h3>
              <p className="text-[12px] font-bold uppercase tracking-wider text-[#45464D]">Academic Lab Tier</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#45464D] hover:text-[#0F172A] p-1 rounded-full hover:bg-[#E0E3E5]"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="space-y-3">
          <div className="p-4 rounded-lg bg-[#F8FAFC] border border-[#C6C6CD] space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-bold text-[16px] text-[#0F172A]">Institutional Research Pro</span>
              <span className="text-[18px] font-bold text-[#0F172A]">$29 <span className="text-[12px] font-normal text-[#45464D]">/ month</span></span>
            </div>
            <p className="text-[13px] text-[#45464D]">
              Designed for individual scholars, university researchers, and lab directors.
            </p>
          </div>

          <ul className="space-y-2 text-[14px] text-[#191C1E] pt-2">
            <li className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#2563EB] text-[18px]">check_circle</span>
              Unlimited Gemini 3.6 Deep Dive literature syntheses
            </li>
            <li className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#2563EB] text-[18px]">check_circle</span>
              Real-time Google Search grounding & DOI indexing
            </li>
            <li className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#2563EB] text-[18px]">check_circle</span>
              BibTeX, Zotero, and RIS automated citation exporter
            </li>
            <li className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#2563EB] text-[18px]">check_circle</span>
              PDF, CSV & JSON dataset knowledge base attachments
            </li>
          </ul>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 px-4 rounded-md border border-[#C6C6CD] text-[#0F172A] font-bold text-[13px] uppercase tracking-wider hover:bg-[#E0E3E5] transition-colors"
          >
            Maybe Later
          </button>
          <button
            onClick={() => {
              alert('Plan upgraded successfully! Welcome to Research Lab Pro.');
              onClose();
            }}
            className="flex-1 py-2.5 px-4 rounded-md bg-[#0F172A] text-white font-bold text-[13px] uppercase tracking-wider hover:bg-slate-800 transition-colors shadow-sm"
          >
            Upgrade Now
          </button>
        </div>
      </div>
    </div>
  );
};
