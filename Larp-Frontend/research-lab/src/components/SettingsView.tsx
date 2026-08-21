// src/components/SettingsView.tsx
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
    <div className="flex-1 overflow-y-auto p-4 md:p-8 bg-[#090D16] text-[#E5E7EB]">
      <div className="max-w-[760px] mx-auto space-y-8">
        {/* Header */}
        <div className="border-b border-[#1B2536] pb-4">
          <h2 className="text-[20px] font-bold text-white">Settings & Preferences</h2>
          <p className="text-[12px] text-zinc-400 mt-0.5">
            Configure default synthesis parameters, export formats, and institutional credentials.
          </p>
        </div>

        {/* Section 1: Research Parameters */}
        <div className="bg-[#0D1525] border border-[#1B2536] rounded-xl p-5 space-y-5 shadow-sm">
          <h3 className="text-[14px] font-bold text-white border-b border-zinc-900 pb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-primary">science</span>
            Research Parameters
          </h3>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="font-semibold text-[13px] text-white">Default Research Mode</h4>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                Set whether new sessions default to Quick Scan or Deep Dive mode.
              </p>
            </div>
            <div className="flex items-center bg-[#070B13] rounded-lg p-0.5 border border-[#1B2536] shrink-0">
              <button
                type="button"
                onClick={() => setDefaultMode('quick')}
                className={`px-3 py-1.5 rounded-md text-[10px] font-bold tracking-wider uppercase cursor-pointer outline-none transition-all ${
                  defaultMode === 'quick'
                    ? 'bg-[#172237] text-white shadow-xs'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Quick Scan
              </button>
              <button
                type="button"
                onClick={() => setDefaultMode('deep')}
                className={`px-3 py-1.5 rounded-md text-[10px] font-bold tracking-wider uppercase cursor-pointer outline-none transition-all ${
                  defaultMode === 'deep'
                    ? 'bg-[#172237] text-white shadow-xs'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Deep Dive
              </button>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-zinc-900 pt-4">
            <div>
              <h4 className="font-semibold text-[13px] text-white">Citation Style Format</h4>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                Default export format for bibliography and references.
              </p>
            </div>
            <select
              value={citationFormat}
              onChange={(e) => setCitationFormat(e.target.value)}
              className="bg-[#070B13] border border-[#1B2536] rounded-lg px-3 py-1.5 text-[12px] font-medium text-white focus:outline-none focus:border-primary shrink-0"
            >
              <option value="IEEE">IEEE Style [1]</option>
              <option value="APA">APA 7th Edition</option>
              <option value="BibTeX">BibTeX / LaTeX</option>
              <option value="MLA">MLA 9th Edition</option>
            </select>
          </div>

          <div className="flex items-center justify-between border-t border-zinc-900 pt-4">
            <div>
              <h4 className="font-semibold text-[13px] text-white">Auto-Cache Reference PDFs</h4>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                Automatically download and index open-access PDF attachments.
              </p>
            </div>
            <input
              type="checkbox"
              checked={autoDownloadPdf}
              onChange={(e) => setAutoDownloadPdf(e.target.checked)}
              className="w-4 h-4 bg-[#070B13] border-[#1B2536] rounded text-primary focus:ring-primary accent-primary cursor-pointer shrink-0"
            />
          </div>
        </div>

        {/* Section 2: Account & License */}
        <div className="bg-[#0D1525] border border-[#1B2536] rounded-xl p-5 space-y-4 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-[14px] font-bold text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-primary">badge</span>
                Institutional Subscription
              </h3>
              <p className="text-[11px] text-zinc-400 mt-1">
                Academic Tier • Research Lab Pro (Active)
              </p>
            </div>
            <span className="bg-emerald-500/10 text-emerald-400 text-[9px] font-bold px-2 py-0.5 rounded-md border border-emerald-500/20 uppercase tracking-wider">
              Active Plan
            </span>
          </div>

          <div className="border-t border-zinc-900 pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <span className="text-[11px] text-zinc-400">
              Unlimited Groq / Tavily Search &amp; BibTeX Exports Enabled
            </span>
            <button
              type="button"
              onClick={onUpgradeClick}
              className="px-3.5 py-2 bg-primary text-white hover:bg-blue-600 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-colors outline-none cursor-pointer"
            >
              Manage Subscription
            </button>
          </div>
        </div>

        {/* Section 3: Payment Wallet (x402) */}
        <div className="bg-[#0D1525] border border-[#1B2536] rounded-xl p-5 space-y-5 shadow-sm">
          <div className="flex items-start justify-between border-b border-zinc-900 pb-3">
            <div>
              <h3 className="text-[14px] font-bold text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-primary">account_balance_wallet</span>
                x402 Payment Wallet
              </h3>
              <p className="text-[11px] text-zinc-400 mt-1">
                Autonomous USDC micropayments for each research pipeline step.
              </p>
            </div>
            <span className={`text-[9px] font-bold px-2 py-0.5 rounded-md border uppercase tracking-wider ${
              globalLog?.mode === 'real'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-primary/10 text-primary border-primary/20'
            }`}>
              {globalLog?.mode === 'real' ? 'Live' : 'Simulation'}
            </span>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-[#070B13] rounded-xl p-3 text-center border border-[#1B2536]">
              <div className="font-mono font-bold text-[16px] text-primary">
                ${sessionTotal}
              </div>
              <div className="text-[9px] text-zinc-500 uppercase tracking-wider font-semibold mt-0.5">Session Spent</div>
            </div>
            <div className="bg-[#070B13] rounded-xl p-3 text-center border border-[#1B2536]">
              <div className="font-mono font-bold text-[16px] text-white">
                {globalLog?.totalTransactions ?? 0}
              </div>
              <div className="text-[9px] text-zinc-500 uppercase tracking-wider font-semibold mt-0.5">Total TXs</div>
            </div>
            <div className="bg-[#070B13] rounded-xl p-3 text-center border border-[#1B2536]">
              <div className="font-mono font-bold text-[16px] text-emerald-400">
                ${globalLog?.totalSpentUSDC ?? '0.0000'}
              </div>
              <div className="text-[9px] text-zinc-500 uppercase tracking-wider font-semibold mt-0.5">All-time USDC</div>
            </div>
          </div>

          {/* Current session receipts */}
          {livePayments.length > 0 && (
            <div className="border-t border-zinc-900 pt-4">
              <h4 className="font-bold text-[11px] text-zinc-400 mb-2.5 uppercase tracking-wider">Current Session Receipts</h4>
              <div className="space-y-2 max-h-[180px] overflow-y-auto pr-0.5">
                {livePayments.map((receipt, i) => (
                  <div key={i} className="flex items-center justify-between bg-[#070B13] border border-[#1B2536] rounded-xl px-3 py-2">
                    <div className="min-w-0">
                      <div className="font-semibold text-[12px] text-white truncate">{receipt.stepName}</div>
                      <div className="font-mono text-[9px] text-zinc-500 truncate mt-0.5">{receipt.txHash}</div>
                    </div>
                    <div className="text-right shrink-0 ml-3">
                      <div className="font-mono font-bold text-[12px] text-emerald-400">{receipt.amount} USDC</div>
                      <div className="text-[9px] text-zinc-500 mt-0.5">{receipt.currency} · {receipt.network.split(' ')[0]}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {livePayments.length === 0 && (
            <p className="text-[12px] text-zinc-500 italic text-center py-2">
              No payments yet. Run a research query to see x402 payment receipts here.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
