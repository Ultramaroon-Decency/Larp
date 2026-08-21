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
  }, [livePayments]);

  const sessionTotal = livePayments
    .reduce((sum, p) => sum + parseFloat(p.amount), 0)
    .toFixed(4);

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#18181B] text-[#F4F4F5]">
      <div className="max-w-[640px] mx-auto space-y-12 pb-12">
        {/* Header */}
        <div className="pb-4">
          <h2 className="text-[24px] font-bold tracking-tight">Settings</h2>
        </div>

        {/* Section 1: Research Parameters */}
        <div className="space-y-4">
          <h3 className="text-[12px] font-bold tracking-wider text-[#76777D] uppercase px-2">
            Research Parameters
          </h3>
          <div className="bg-[#18181B] border border-[#27272A] rounded-xl overflow-hidden divide-y divide-[#27272A]">
            
            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-[#27272A] transition-colors">
              <div>
                <h4 className="font-medium text-[14px]">Default Mode</h4>
                <p className="text-[13px] text-[#A1A1AA] mt-0.5">
                  Initial depth for new queries.
                </p>
              </div>
              <div className="flex items-center bg-[#18181B] rounded-lg p-1 border border-[#3F3F46] mt-3 sm:mt-0">
                <button
                  type="button"
                  onClick={() => setDefaultMode('quick')}
                  className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-colors ${
                    defaultMode === 'quick'
                      ? 'bg-[#3F3F46] text-[#F4F4F5]'
                      : 'text-[#A1A1AA] hover:text-[#F4F4F5]'
                  }`}
                >
                  Quick Scan
                </button>
                <button
                  type="button"
                  onClick={() => setDefaultMode('deep')}
                  className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-colors ${
                    defaultMode === 'deep'
                      ? 'bg-[#3F3F46] text-[#F4F4F5]'
                      : 'text-[#A1A1AA] hover:text-[#F4F4F5]'
                  }`}
                >
                  Deep Dive
                </button>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-[#27272A] transition-colors">
              <div>
                <h4 className="font-medium text-[14px]">Citation Style</h4>
                <p className="text-[13px] text-[#A1A1AA] mt-0.5">
                  Export format for bibliography.
                </p>
              </div>
              <select
                value={citationFormat}
                onChange={(e) => setCitationFormat(e.target.value)}
                className="mt-3 sm:mt-0 bg-[#18181B] border border-[#3F3F46] rounded-lg px-3 py-1.5 text-[13px] text-[#F4F4F5] focus:outline-none focus:border-[#10B981] cursor-pointer"
              >
                <option value="IEEE">IEEE Style</option>
                <option value="APA">APA 7th Edition</option>
                <option value="BibTeX">BibTeX / LaTeX</option>
                <option value="MLA">MLA 9th Edition</option>
              </select>
            </div>

            <div className="flex items-center justify-between p-4 hover:bg-[#27272A] transition-colors">
              <div>
                <h4 className="font-medium text-[14px]">Auto-Cache PDFs</h4>
                <p className="text-[13px] text-[#A1A1AA] mt-0.5">
                  Download open-access attachments.
                </p>
              </div>
              <input
                type="checkbox"
                checked={autoDownloadPdf}
                onChange={(e) => setAutoDownloadPdf(e.target.checked)}
                className="w-5 h-5 accent-[#10B981] cursor-pointer"
              />
            </div>

          </div>
        </div>

        {/* Section 2: Account & Subscription */}
        <div className="space-y-4">
          <h3 className="text-[12px] font-bold tracking-wider text-[#76777D] uppercase px-2">
            Account & Subscription
          </h3>
          <div className="bg-[#18181B] border border-[#27272A] rounded-xl overflow-hidden divide-y divide-[#27272A]">
            
            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-[#27272A] transition-colors">
              <div>
                <h4 className="font-medium text-[14px]">Research Lab Pro</h4>
                <p className="text-[13px] text-[#A1A1AA] mt-0.5">
                  Institutional Tier
                </p>
              </div>
              <div className="flex items-center gap-4 mt-3 sm:mt-0">
                <span className="text-[11px] font-bold text-[#10B981] bg-[#10B981]/10 px-2.5 py-1 rounded-md uppercase tracking-wider">
                  Active
                </span>
                <button
                  type="button"
                  onClick={onUpgradeClick}
                  className="px-3 py-1.5 bg-[#27272A] border border-[#3F3F46] hover:bg-[#3F3F46] text-[#F4F4F5] text-[12px] font-medium rounded-lg transition-colors"
                >
                  Manage
                </button>
              </div>
            </div>

          </div>
        </div>

        {/* Section 3: Wallet */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-[12px] font-bold tracking-wider text-[#76777D] uppercase">
              x402 Wallet
            </h3>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${
              globalLog?.mode === 'real'
                ? 'bg-[#10B981]/10 text-[#10B981]'
                : 'bg-[#3F3F46] text-[#A1A1AA]'
            }`}>
              {globalLog?.mode === 'real' ? 'Live' : 'Simulation'}
            </span>
          </div>
          
          <div className="bg-[#18181B] border border-[#27272A] rounded-xl overflow-hidden">
            <div className="grid grid-cols-3 divide-x divide-[#27272A] border-b border-[#27272A]">
              <div className="p-4 text-center hover:bg-[#27272A] transition-colors">
                <div className="font-mono text-[16px] text-[#F4F4F5]">
                  ${sessionTotal}
                </div>
                <div className="text-[11px] text-[#76777D] mt-1">Session</div>
              </div>
              <div className="p-4 text-center hover:bg-[#27272A] transition-colors">
                <div className="font-mono text-[16px] text-[#F4F4F5]">
                  {globalLog?.totalTransactions ?? 0}
                </div>
                <div className="text-[11px] text-[#76777D] mt-1">Total TXs</div>
              </div>
              <div className="p-4 text-center hover:bg-[#27272A] transition-colors">
                <div className="font-mono text-[16px] text-[#F4F4F5]">
                  ${globalLog?.totalSpentUSDC ?? '0.0000'}
                </div>
                <div className="text-[11px] text-[#76777D] mt-1">All-time</div>
              </div>
            </div>

            <div className="p-4">
              {livePayments.length > 0 ? (
                <div className="space-y-2 max-h-[200px] overflow-y-auto pr-2">
                  {livePayments.map((receipt, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-[#27272A] last:border-0">
                      <div className="min-w-0 flex-1">
                        <div className="text-[13px] text-[#D4D4D8] truncate">{receipt.stepName}</div>
                        <div className="font-mono text-[10px] text-[#76777D] truncate">{receipt.txHash}</div>
                      </div>
                      <div className="text-right shrink-0 ml-4">
                        <div className="font-mono text-[13px] text-[#10B981]">{receipt.amount} USDC</div>
                        <div className="text-[10px] text-[#76777D]">{receipt.network}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-[13px] text-[#76777D] text-center py-4">
                  No payments in current session.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
