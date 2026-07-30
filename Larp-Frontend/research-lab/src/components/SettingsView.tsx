import React, { useState, useEffect } from 'react';
import { ResearchMode, PaymentReceipt } from '../types';

interface SettingsViewProps {
  defaultMode: ResearchMode;
  setDefaultMode: (mode: ResearchMode) => void;
  onUpgradeClick: () => void;
  livePayments: PaymentReceipt[];
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  defaultMode,
  setDefaultMode,
  onUpgradeClick,
  livePayments,
}) => {
  const [citationFormat, setCitationFormat] = useState('IEEE');
  const [autoDownloadPdf, setAutoDownloadPdf] = useState(true);
  const [themeMode, setThemeMode] = useState<'light' | 'dark' | 'system'>('light');
  const [globalLog, setGlobalLog] = useState<{
    mode: string;
    totalTransactions: number;
    totalSpentUSDC: string;
    receipts: (PaymentReceipt & { sessionId: string })[];
  } | null>(null);

  useEffect(() => {
    fetch('/api/payments/log')
      .then((r) => r.json())
      .then(setGlobalLog)
      .catch(() => {/* silently ignore if server isn't up */});
  }, [livePayments]); // refresh whenever a new payment arrives

  const sessionTotal = livePayments
    .reduce((sum, p) => sum + parseFloat(p.amount), 0)
    .toFixed(4);

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#F7F9FB]">
      <div className="max-w-[840px] mx-auto space-y-8">
        {/* Header */}
        <div className="border-b border-[#C6C6CD] pb-4">
          <h2 className="text-[24px] font-bold text-[#0F172A]">Settings & Preferences</h2>
          <p className="text-[14px] text-[#45464D] mt-0.5">
            Configure default synthesis parameters, export formats, and institutional credentials.
          </p>
        </div>

        {/* Section 1: Research Parameters */}
        <div className="bg-white border border-[#C6C6CD] rounded-lg p-6 space-y-6 shadow-2xs">
          <h3 className="text-[16px] font-bold text-[#0F172A] border-b border-[#C6C6CD]/50 pb-2">
            Synthesis & Vector Parameters
          </h3>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="font-bold text-[15px] text-[#0F172A]">Default Research Mode</h4>
              <p className="text-[13px] text-[#45464D] mt-0.5">
                Set whether new sessions default to Quick Scan or Deep Dive mode.
              </p>
            </div>
            <div className="flex items-center bg-[#F2F4F6] rounded-md p-1 border border-[#C6C6CD]">
              <button
                type="button"
                onClick={() => setDefaultMode('quick')}
                className={`px-3 py-1.5 rounded-md text-[11px] font-bold tracking-wider uppercase cursor-pointer ${
                  defaultMode === 'quick'
                    ? 'bg-white border border-[#C6C6CD] shadow-xs text-[#0F172A]'
                    : 'text-[#45464D]'
                }`}
              >
                Quick Scan
              </button>
              <button
                type="button"
                onClick={() => setDefaultMode('deep')}
                className={`px-3 py-1.5 rounded-md text-[11px] font-bold tracking-wider uppercase cursor-pointer ${
                  defaultMode === 'deep'
                    ? 'bg-white border border-[#C6C6CD] shadow-xs text-[#0F172A]'
                    : 'text-[#45464D]'
                }`}
              >
                Deep Dive
              </button>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-[#C6C6CD]/40 pt-4">
            <div>
              <h4 className="font-bold text-[15px] text-[#0F172A]">Citation Style Format</h4>
              <p className="text-[13px] text-[#45464D] mt-0.5">
                Default export format for bibliography and references.
              </p>
            </div>
            <select
              value={citationFormat}
              onChange={(e) => setCitationFormat(e.target.value)}
              className="bg-white border border-[#C6C6CD] rounded-md px-3 py-1.5 text-[14px] font-medium text-[#0F172A] focus:outline-none focus:border-[#0F172A]"
            >
              <option value="IEEE">IEEE Style [1]</option>
              <option value="APA">APA 7th Edition</option>
              <option value="BibTeX">BibTeX / LaTeX</option>
              <option value="MLA">MLA 9th Edition</option>
            </select>
          </div>

          <div className="flex items-center justify-between border-t border-[#C6C6CD]/40 pt-4">
            <div>
              <h4 className="font-bold text-[15px] text-[#0F172A]">Auto-Cache Reference PDFs</h4>
              <p className="text-[13px] text-[#45464D] mt-0.5">
                Automatically download and index open-access PDF attachments.
              </p>
            </div>
            <input
              type="checkbox"
              checked={autoDownloadPdf}
              onChange={(e) => setAutoDownloadPdf(e.target.checked)}
              className="w-5 h-5 accent-[#0F172A] cursor-pointer"
            />
          </div>
        </div>

        {/* Section 2: Account & License */}
        <div className="bg-white border border-[#C6C6CD] rounded-lg p-6 space-y-4 shadow-2xs">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-[16px] font-bold text-[#0F172A]">Institutional Subscription</h3>
              <p className="text-[13px] text-[#45464D] mt-1">
                Academic Tier • Research Lab Pro (Active)
              </p>
            </div>
            <span className="bg-emerald-100 text-emerald-800 text-[11px] font-bold px-2.5 py-1 rounded border border-emerald-200 uppercase tracking-wider">
              Active Plan
            </span>
          </div>

          <div className="border-t border-[#C6C6CD]/40 pt-4 flex items-center justify-between">
            <span className="text-[13px] text-[#45464D]">
              Unlimited Groq / Tavily Search &amp; BibTeX Exports Enabled
            </span>
            <button
              type="button"
              onClick={onUpgradeClick}
              className="px-4 py-2 border border-[#0F172A] bg-[#0F172A] text-white text-[12px] font-bold uppercase tracking-wider rounded-md hover:bg-slate-800 transition-colors"
            >
              Manage Subscription
            </button>
          </div>
        </div>
        {/* Section 3: Payment Wallet (x402) */}
        <div className="bg-white border border-[#C6C6CD] rounded-lg p-6 space-y-4 shadow-2xs">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-[16px] font-bold text-[#0F172A]">x402 Payment Wallet</h3>
              <p className="text-[13px] text-[#45464D] mt-1">
                Autonomous USDC micropayments for each research pipeline step.
              </p>
            </div>
            <span className={`text-[11px] font-bold px-2.5 py-1 rounded border uppercase tracking-wider ${
              globalLog?.mode === 'real'
                ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                : 'bg-blue-100 text-blue-800 border-blue-200'
            }`}>
              {globalLog?.mode === 'real' ? 'Live' : 'Simulation'}
            </span>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-[#F2F4F6] rounded-md p-3 text-center border border-[#E0E3E5]">
              <div className="font-mono font-bold text-[18px] text-[#0F172A]">
                ${sessionTotal}
              </div>
              <div className="text-[11px] text-[#45464D] uppercase tracking-wider mt-0.5">Session Spent</div>
            </div>
            <div className="bg-[#F2F4F6] rounded-md p-3 text-center border border-[#E0E3E5]">
              <div className="font-mono font-bold text-[18px] text-[#0F172A]">
                {globalLog?.totalTransactions ?? 0}
              </div>
              <div className="text-[11px] text-[#45464D] uppercase tracking-wider mt-0.5">Total TXs</div>
            </div>
            <div className="bg-[#F2F4F6] rounded-md p-3 text-center border border-[#E0E3E5]">
              <div className="font-mono font-bold text-[18px] text-[#0F172A]">
                ${globalLog?.totalSpentUSDC ?? '0.0000'}
              </div>
              <div className="text-[11px] text-[#45464D] uppercase tracking-wider mt-0.5">All-time USDC</div>
            </div>
          </div>

          {/* Current session receipts */}
          {livePayments.length > 0 && (
            <div className="border-t border-[#C6C6CD]/40 pt-4">
              <h4 className="font-bold text-[13px] text-[#0F172A] mb-2 uppercase tracking-wider">Current Session Receipts</h4>
              <div className="space-y-1.5 max-h-[180px] overflow-y-auto">
                {livePayments.map((receipt, i) => (
                  <div key={i} className="flex items-center justify-between bg-[#F7F9FB] border border-[#E0E3E5] rounded px-3 py-2">
                    <div className="min-w-0">
                      <div className="font-bold text-[12px] text-[#0F172A] truncate">{receipt.stepName}</div>
                      <div className="font-mono text-[10px] text-[#76777D] truncate">{receipt.txHash.substring(0, 22)}...</div>
                    </div>
                    <div className="text-right shrink-0 ml-3">
                      <div className="font-mono font-bold text-[13px] text-emerald-700">{receipt.amount} USDC</div>
                      <div className="text-[10px] text-[#76777D]">{receipt.currency} · {receipt.network.split(' ')[0]}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {livePayments.length === 0 && (
            <p className="text-[13px] text-[#76777D] italic text-center py-2">
              No payments yet. Run a research query to see x402 payment receipts here.
            </p>
          )}
        </div>

      </div>
    </div>
  );
};
