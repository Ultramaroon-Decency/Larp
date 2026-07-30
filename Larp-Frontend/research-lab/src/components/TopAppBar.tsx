import React from 'react';
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
  onNewResearchClick
}) => {
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

  return (
    <header className="sticky top-0 z-10 bg-[#F7F9FB] border-b border-[#C6C6CD] flex justify-between items-center h-16 px-6 w-full shrink-0">
      {/* Mobile Menu Toggle & Title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onOpenMobileMenu}
          className="md:hidden text-[#45464D] hover:text-[#0F172A] p-2 rounded-md hover:bg-[#E0E3E5] transition-colors"
          title="Toggle menu"
        >
          <span className="material-symbols-outlined">menu</span>
        </button>

        <div className="flex items-center gap-2 truncate">
          {activeTab === 'library' && (
            <span className="material-symbols-outlined text-[#0F172A] fill-1">book</span>
          )}
          {activeTab === 'bibliography' && (
            <span className="material-symbols-outlined text-[#0F172A]">description</span>
          )}
          <h2 className="font-bold text-[18px] text-[#0F172A] truncate">
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
              className="text-[12px] font-bold tracking-wider text-[#45464D] hover:text-[#0F172A] uppercase transition-colors cursor-pointer"
            >
              Export PDF
            </button>
            <button
              onClick={onShare}
              className="text-[12px] font-bold tracking-wider text-[#45464D] hover:text-[#0F172A] uppercase transition-colors cursor-pointer"
            >
              Share
            </button>
            <button
              onClick={onArchive}
              className="text-[12px] font-bold tracking-wider text-[#45464D] hover:text-[#0F172A] uppercase transition-colors cursor-pointer"
            >
              Archive
            </button>
          </nav>
        )}

        {(activeTab === 'library' || activeTab === 'history') && (
          <div className="relative hidden sm:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#45464D] text-[18px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={activeTab === 'library' ? 'Search library...' : 'Search history...'}
              className="pl-9 pr-4 py-1.5 bg-[#F7F9FB] text-[14px] text-[#191C1E] border border-[#C6C6CD] rounded-md focus:outline-none focus:border-[#0F172A] focus:ring-1 focus:ring-[#0F172A] w-56 sm:w-64 transition-all"
            />
          </div>
        )}

        {activeTab === 'new' && (
          <button
            onClick={onNewResearchClick}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 border border-[#C6C6CD] rounded-md text-[12px] font-bold uppercase tracking-wider text-[#0F172A] hover:bg-[#E0E3E5] transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            Reset Form
          </button>
        )}

        {/* Profile & Options Icons */}
        <div className="flex items-center gap-2 border-l border-[#C6C6CD] pl-3">
          <button
            onClick={onShare}
            className="text-[#45464D] hover:text-[#0F172A] p-1.5 rounded-full hover:bg-[#E0E3E5] transition-colors"
            title="More Options"
          >
            <span className="material-symbols-outlined text-[20px]">more_vert</span>
          </button>
          <div
            className="w-8 h-8 rounded-full bg-[#0F172A] text-white flex items-center justify-center font-bold text-[13px] border border-[#C6C6CD] cursor-pointer"
            title="User Profile"
          >
            <span className="material-symbols-outlined text-[20px]">account_circle</span>
          </div>
        </div>
      </div>
    </header>
  );
};
