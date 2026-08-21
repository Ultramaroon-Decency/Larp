// src/components/Sidebar.tsx
import React from 'react';
import { ActiveTab, ResearchProject } from '../types';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  isOpenMobile: boolean;
  setIsOpenMobile: (open: boolean) => void;
  onUpgradeClick: () => void;
  onNewResearchClick: () => void;
  projects?: ResearchProject[];
  onSelectProject?: (project: ResearchProject) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isOpenMobile,
  setIsOpenMobile,
  onUpgradeClick,
  onNewResearchClick,
  projects = [],
  onSelectProject
}) => {
  const handleTabClick = (tab: ActiveTab) => {
    if (tab === 'new') {
      onNewResearchClick();
    } else {
      setActiveTab(tab);
    }
    setIsOpenMobile(false);
  };

  const handleRecentClick = (project: ResearchProject) => {
    if (onSelectProject) {
      onSelectProject(project);
    }
    setIsOpenMobile(false);
  };

  // Keep navigation items clean and unified
  const topNavItems: { id: ActiveTab; label: string; icon: string }[] = [
    { id: 'new', label: 'New Chat', icon: 'add' },
  ];

  const bottomNavItems: { id: ActiveTab; label: string; icon: string; fillIcon?: boolean }[] = [
    { id: 'library', label: 'Library', icon: 'book', fillIcon: activeTab === 'library' || activeTab === 'bibliography' },
    { id: 'history', label: 'History', icon: 'history' },
    { id: 'settings', label: 'Settings', icon: 'settings' }
  ];

  // Select the last 6 recent research sessions to show in sidebar
  const recentProjects = projects.slice(0, 6);

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#070B13] text-[#E5E7EB] font-sans">
      {/* Brand Header */}
      <div className="p-4 pt-6 pb-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold">
          <span className="material-symbols-outlined text-[18px]">science</span>
        </div>
        <div className="min-w-0">
          <h1 className="text-[15px] font-bold text-white tracking-tight leading-none">Research Lab</h1>
          <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-semibold mt-0.5">Academic OS</p>
        </div>
      </div>

      {/* Primary Actions (New Chat / New Research) */}
      <div className="px-3 mb-4">
        <button
          onClick={() => handleTabClick('new')}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-[#111A2E] hover:bg-[#1A263E] border border-primary/20 hover:border-primary/40 text-primary font-semibold text-[13px] transition-all duration-200 text-left outline-none cursor-pointer group shadow-xs"
        >
          <span className="material-symbols-outlined text-[18px] group-hover:scale-110 transition-transform">add</span>
          <span>New Research</span>
        </button>
      </div>

      {/* Scrollable Navigation Body */}
      <div className="flex-1 overflow-y-auto px-2 space-y-6 scrollbar-none">
        {/* Recent Section */}
        {recentProjects.length > 0 && (
          <div className="space-y-1">
            <div className="px-3 mb-1.5 flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-500">Recent Threads</span>
            </div>
            <div className="space-y-0.5">
              {recentProjects.map((project) => {
                const isProjectActive = activeTab === 'chat' && project.id === projects.find((p) => p.title === project.title)?.id;
                return (
                  <button
                    key={project.id}
                    onClick={() => handleRecentClick(project)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-[13px] transition-all duration-150 outline-none cursor-pointer ${
                      isProjectActive
                        ? 'bg-[#18233C]/80 text-white font-medium'
                        : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[16px] text-zinc-500 shrink-0">chat_bubble</span>
                    <span className="truncate flex-1">{project.title}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Pinned Bottom Controls & Account Options */}
      <div className="p-2 border-t border-zinc-900 bg-black/10">
        <nav className="space-y-0.5 mb-2">
          {bottomNavItems.map((item) => {
            const isActive =
              item.id === 'library'
                ? activeTab === 'library' || activeTab === 'bibliography'
                : activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-[13px] transition-all duration-150 outline-none cursor-pointer ${
                  isActive
                    ? 'bg-[#18233C]/80 text-white font-medium'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40'
                }`}
              >
                <span
                  className={`material-symbols-outlined text-[18px] shrink-0 text-zinc-500 ${
                    item.fillIcon || isActive ? 'fill-1 text-primary' : ''
                  }`}
                >
                  {item.icon}
                </span>
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Upgrade Plan Button */}
        <button
          onClick={onUpgradeClick}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[12px] font-medium text-zinc-300 transition-colors cursor-pointer"
        >
          <span className="material-symbols-outlined text-[16px] text-amber-500">workspace_premium</span>
          Upgrade to Pro
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar Rail */}
      <aside className="w-[240px] h-screen sticky left-0 top-0 border-r border-[#1B2536] hidden md:flex flex-col shrink-0 z-20 overflow-hidden shadow-xl">
        {sidebarContent}
      </aside>

      {/* Mobile Sidebar Overlay & Drawer */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs"
            onClick={() => setIsOpenMobile(false)}
          />
          <aside className="relative w-[240px] h-full flex flex-col z-10 shadow-2xl border-r border-zinc-900">
            <button
              onClick={() => setIsOpenMobile(false)}
              className="absolute top-4 right-4 p-1 text-zinc-400 hover:text-white rounded-full hover:bg-zinc-900"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};
