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
    title = 'New Research Protocol';
  } else if (activeTab === 'chat' && activeProject) {
    title = 'Research Assistant';
  } else if (activeTab === 'library') {
    title = 'Saved Library';
  } else if (activeTab === 'bibliography' && activeProject) {
    title = activeProject.title || 'Sources & Bibliography';
  } else if (activeTab === 'history') {
    title = 'Research History';
  } else if (activeTab === 'settings') {
    title = 'Settings & Preferences';
  }

  const userInitial = authUser?.name ? authUser.name.charAt(0).toUpperCase() : null;

  return (
    <header className="bg-surface dark:bg-background sticky top-0 border-b border-outline-variant dark:border-outline flex justify-between items-center h-16 px-gutter w-full z-10 shrink-0">
      {/* Mobile Menu Toggle & Title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onOpenMobileMenu}
          className="md:hidden text-on-surface-variant hover:text-primary p-2 mr-2 rounded-md hover:bg-surface-variant transition-colors"
          title="Toggle menu"
        >
          <span className="material-symbols-outlined">menu</span>
        </button>

        <div className="flex items-center gap-2 truncate">
          {activeTab === 'library' && (
            <span className="material-symbols-outlined text-primary fill-1">book</span>
          )}
          {activeTab === 'bibliography' && (
            <span className="material-symbols-outlined text-primary">description</span>
          )}
          <h2 className="font-headline-md text-headline-md font-bold text-primary dark:text-primary-fixed truncate">
            {title}
          </h2>
        </div>
      </div>

      {/* Global Actions Contextual to Current Tab */}
      <div className="flex items-center gap-4 shrink-0">
        {(activeTab === 'chat' || activeTab === 'bibliography') && (
          <nav className="hidden sm:flex items-center gap-6">
            <button
              onClick={onExportPdf}
              className="text-label-caps font-label-caps text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
            >
              Export PDF
            </button>
            <button
              onClick={onShare}
              className="text-label-caps font-label-caps text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
            >
              Share
            </button>
            <button
              onClick={onArchive}
              className="text-label-caps font-label-caps text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
            >
              Archive
            </button>
          </nav>
        )}

        {(activeTab === 'library' || activeTab === 'history') && (
          <div className="relative hidden sm:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={activeTab === 'library' ? 'Search library...' : 'Search history...'}
              className="pl-9 pr-4 py-1.5 bg-surface text-body-md border border-outline-variant rounded-DEFAULT focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary w-56 sm:w-64 placeholder-on-surface-variant transition-all"
            />
          </div>
        )}

        {activeTab === 'new' && (
          <button
            onClick={onNewResearchClick}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 border border-outline-variant rounded-DEFAULT text-label-caps font-label-caps text-primary hover:bg-surface-variant transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            Reset Form
          </button>
        )}

        {/* Profile & Options Icons */}
        <div className="flex items-center gap-2">
          <button
            onClick={onShare}
            className="text-on-surface-variant hover:text-primary transition-colors p-2 rounded-full hover:bg-surface-variant"
            title="More Options"
          >
            <span className="material-symbols-outlined">more_vert</span>
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
              className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors p-1 rounded-full hover:bg-surface-variant cursor-pointer"
              title={authUser ? authUser.name : 'Sign In'}
            >
              {authUser && userInitial ? (
                <div className="w-[30px] h-[30px] rounded-full bg-primary text-on-primary flex items-center justify-center text-[14px] font-bold">
                  {userInitial}
                </div>
              ) : (
                <span className="material-symbols-outlined text-[28px]">account_circle</span>
              )}
            </button>

            {/* Profile Dropdown Menu */}
            {showProfileMenu && authUser && (
              <div className="absolute right-0 top-full mt-2 w-64 bg-surface border border-outline-variant rounded-xl shadow-xl overflow-hidden z-50">
                {/* User Info */}
                <div className="px-4 py-3 border-b border-outline-variant">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary text-on-primary flex items-center justify-center text-[16px] font-bold shrink-0">
                      {userInitial}
                    </div>
                    <div className="min-w-0">
                      <p className="text-[14px] font-semibold text-on-surface truncate">{authUser.name}</p>
                      <p className="text-[12px] text-on-surface-variant truncate">{authUser.email}</p>
                    </div>
                  </div>
                </div>

                {/* Menu Items */}
                <div className="py-1">
                  <button
                    onClick={() => { setShowProfileMenu(false); onProfileClick?.(); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-[13px] text-on-surface hover:bg-surface-container-low transition-colors cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[18px] text-on-surface-variant">settings</span>
                    Account Settings
                  </button>
                  <button
                    onClick={() => { setShowProfileMenu(false); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-[13px] text-on-surface hover:bg-surface-container-low transition-colors cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[18px] text-on-surface-variant">account_balance_wallet</span>
                    Wallet & Payments
                  </button>
                  <div className="h-px bg-outline-variant mx-3 my-1" />
                  <button
                    onClick={() => { setShowProfileMenu(false); onLogout?.(); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-[13px] text-error hover:bg-error-container transition-colors cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[18px]">logout</span>
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
