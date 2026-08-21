// src/components/TopAppBar.tsx
import React, { useState, useRef, useEffect } from 'react';
import { ActiveTab, ResearchProject } from '../types';

interface TopAppBarProps {
  activeTab: ActiveTab;
  activeProject: ResearchProject | null;
  onOpenMobileMenu: () => void;
  onExportPdf: () => void;
  onShare: () => void;
  onArchive: () => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  onNewResearchClick: () => void;
  authUser?: { email: string; name: string } | null;
  onProfileClick?: () => void;
  onLogout?: () => void;
}

export const TopAppBar: React.FC<TopAppBarProps> = ({
  activeTab,
  activeProject,
  onOpenMobileMenu,
  onExportPdf,
  onShare,
  onArchive,
  searchQuery,
  setSearchQuery,
  onNewResearchClick,
  authUser,
  onProfileClick,
  onLogout
}) => {
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  let title = 'Research Lab';
  if (activeTab === 'new') {
    title = 'New Research';
  } else if (activeTab === 'chat' && activeProject) {
    title = activeProject.title || 'Research Assistant';
  } else if (activeTab === 'library') {
    title = 'Library';
  } else if (activeTab === 'bibliography' && activeProject) {
    title = 'Sources';
  } else if (activeTab === 'history') {
    title = 'History';
  } else if (activeTab === 'settings') {
    title = 'Settings';
  }

  const userInitial = authUser?.name ? authUser.name.charAt(0).toUpperCase() : null;

  return (
    <header className="bg-[#090D16]/95 backdrop-blur-md sticky top-0 border-b border-[#1B2536] flex justify-between items-center h-14 px-6 w-full z-10 shrink-0">
      {/* Mobile Menu Toggle & Title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onOpenMobileMenu}
          className="md:hidden text-zinc-400 hover:text-white p-1.5 mr-1 rounded-lg hover:bg-zinc-900 transition-colors cursor-pointer outline-none"
          title="Toggle menu"
        >
          <span className="material-symbols-outlined text-[20px]">menu</span>
        </button>

        <div className="flex items-center gap-2 truncate">
          {activeTab === 'library' && (
            <span className="material-symbols-outlined text-primary text-[18px]">book</span>
          )}
          {activeTab === 'bibliography' && (
            <span className="material-symbols-outlined text-primary text-[18px]">description</span>
          )}
          <h2 className="font-semibold text-[14px] text-white tracking-tight truncate">
            {title}
          </h2>
        </div>
      </div>

      {/* Global Actions Contextual to Current Tab */}
      <div className="flex items-center gap-4 shrink-0">
        {(activeTab === 'chat' || activeTab === 'bibliography') && (
          <nav className="hidden sm:flex items-center gap-5">
            <button
              onClick={onExportPdf}
              className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 hover:text-white transition-colors cursor-pointer outline-none"
            >
              Export PDF
            </button>
            <button
              onClick={onShare}
              className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 hover:text-white transition-colors cursor-pointer outline-none"
            >
              Share
            </button>
            <button
              onClick={onArchive}
              className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 hover:text-white transition-colors cursor-pointer outline-none"
            >
              Archive
            </button>
          </nav>
        )}

        {(activeTab === 'library' || activeTab === 'history') && (
          <div className="relative hidden sm:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 text-[16px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={activeTab === 'library' ? 'Search library...' : 'Search history...'}
              className="pl-8 pr-4 py-1.5 bg-[#0D1525] text-[12px] border border-[#1B2536] rounded-lg focus:outline-none focus:border-primary w-48 sm:w-56 placeholder-zinc-500 transition-all text-white"
            />
          </div>
        )}

        {activeTab === 'new' && (
          <button
            onClick={onNewResearchClick}
            className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 border border-[#1B2536] rounded-lg text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors outline-none cursor-pointer"
          >
            <span className="material-symbols-outlined text-[13px]">refresh</span>
            Reset
          </button>
        )}

        {/* Profile & Options Icons */}
        <div className="flex items-center gap-2">
          <button
            onClick={onShare}
            className="text-zinc-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-zinc-900 outline-none cursor-pointer"
            title="More Options"
          >
            <span className="material-symbols-outlined text-[18px]">more_vert</span>
          </button>

          {/* Profile Button */}
          <div className="relative" ref={profileMenuRef}>
            <button
              onClick={() => {
                if (authUser) {
                  setShowProfileMenu(!showProfileMenu);
                } else {
                  onProfileClick?.();
                }
              }}
              className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors p-0.5 rounded-full hover:bg-zinc-900 cursor-pointer outline-none"
              title={authUser ? authUser.name : 'Sign In'}
            >
              {authUser && userInitial ? (
                <div className="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-[11px] font-bold">
                  {userInitial}
                </div>
              ) : (
                <span className="material-symbols-outlined text-[24px]">account_circle</span>
              )}
            </button>

            {/* Profile Dropdown Menu */}
            {showProfileMenu && authUser && (
              <div className="absolute right-0 top-full mt-2 w-60 bg-[#0D1626] border border-[#1B2536] rounded-xl shadow-xl overflow-hidden z-50">
                {/* User Info */}
                <div className="px-4 py-3 border-b border-[#1B2536] bg-black/10">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-[13px] font-bold shrink-0">
                      {userInitial}
                    </div>
                    <div className="min-w-0">
                      <p className="text-[12px] font-semibold text-white truncate">{authUser.name}</p>
                      <p className="text-[10px] text-zinc-400 truncate">{authUser.email}</p>
                    </div>
                  </div>
                </div>

                {/* Menu Items */}
                <div className="py-1 bg-[#0D1626]">
                  <button
                    onClick={() => { setShowProfileMenu(false); onProfileClick?.(); }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-[12px] text-zinc-300 hover:text-white hover:bg-[#172237] transition-colors cursor-pointer outline-none text-left"
                  >
                    <span className="material-symbols-outlined text-[16px] text-zinc-400">settings</span>
                    Account Settings
                  </button>
                  <button
                    onClick={() => { setShowProfileMenu(false); }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-[12px] text-zinc-300 hover:text-white hover:bg-[#172237] transition-colors cursor-pointer outline-none text-left"
                  >
                    <span className="material-symbols-outlined text-[16px] text-zinc-400">account_balance_wallet</span>
                    Wallet & Payments
                  </button>
                  <div className="h-px bg-[#1B2536] mx-3 my-1" />
                  <button
                    onClick={() => { setShowProfileMenu(false); onLogout?.(); }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-[12px] text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer outline-none text-left"
                  >
                    <span className="material-symbols-outlined text-[16px]">logout</span>
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
