// src/components/UpgradeModal.tsx
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
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative bg-[#0D1626] rounded-xl border border-[#1B2536] shadow-2xl max-w-md w-full p-6 z-10 space-y-6 text-[#E5E7EB] animate-fade-in-down">
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/25 text-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">bolt</span>
            </div>
            <div>
              <h3 className="text-[16px] font-bold text-white leading-none">Upgrade Plan</h3>
              <p className="text-[9px] font-bold uppercase tracking-wider text-zinc-400 mt-1">Academic Lab Tier</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-zinc-900 outline-none"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-[#070B13] border border-[#1B2536] space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-[14px] text-white">Research Pro</span>
              <span className="text-[16px] font-bold text-white">$29 <span className="text-[11px] font-normal text-zinc-500">/ mo</span></span>
            </div>
            <p className="text-[11px] text-zinc-400 leading-relaxed">
              Designed for individual scholars, university researchers, and lab directors.
            </p>
          </div>

          <ul className="space-y-2.5 text-[13px] text-zinc-300 pt-1">
            <li className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[16px]">check_circle</span>
              Unlimited Deep Dive literature syntheses
            </li>
            <li className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[16px]">check_circle</span>
              Real-time Google Search grounding
            </li>
            <li className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[16px]">check_circle</span>
              BibTeX Zotero citation exporter
            </li>
            <li className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[16px]">check_circle</span>
              PDF, CSV & JSON reference uploads
            </li>
          </ul>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            onClick={onClose}
            className="flex-1 py-2 px-3 rounded-lg border border-[#1B2536] hover:border-zinc-700 text-zinc-300 hover:text-white font-bold text-[11px] uppercase tracking-wider transition-colors outline-none cursor-pointer"
          >
            Maybe Later
          </button>
          <button
            onClick={() => {
              alert('Plan upgraded successfully! Welcome to Research Lab Pro.');
              onClose();
            }}
            className="flex-1 py-2 px-3 rounded-lg bg-primary text-white hover:bg-blue-600 font-bold text-[11px] uppercase tracking-wider transition-colors shadow-md outline-none cursor-pointer"
          >
            Upgrade Now
          </button>
        </div>
      </div>
    </div>
  );
};
