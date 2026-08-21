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
  activeProjectId?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isOpenMobile,
  setIsOpenMobile,
  onUpgradeClick,
  onNewResearchClick,
  projects = [],
  onSelectProject,
  activeProjectId
}) => {
  const handleTabClick = (tab: ActiveTab) => {
    if (tab === 'new') {
      onNewResearchClick();
    } else {
      setActiveTab(tab);
    }
    setIsOpenMobile(false);
  };

  const navItems: { id: ActiveTab; label: string; icon: string; fillIcon?: boolean }[] = [
    { id: 'library', label: 'Library', icon: 'book', fillIcon: activeTab === 'library' || activeTab === 'bibliography' },
    { id: 'history', label: 'History', icon: 'history' },
    { id: 'settings', label: 'Settings', icon: 'settings' }
  ];

  const recentProjects = projects.slice(0, 7); // Show top 7 recent projects

  const content = (
    <div className="flex flex-col h-full bg-[#18181B] text-[#F4F4F5]">
      {/* Header */}
      <div className="p-4 flex items-center gap-2 cursor-pointer hover:bg-[#27272A] transition-colors rounded-lg mx-2 mt-2" onClick={onNewResearchClick}>
        <div className="w-8 h-8 rounded-md bg-[#10B981] flex items-center justify-center text-[#18181B]">
          <span className="material-symbols-outlined text-[18px]">science</span>
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-[14px] font-bold tracking-tight text-[#F4F4F5] truncate">Research Lab</h1>
        </div>
        <span className="material-symbols-outlined text-[18px] text-[#A1A1AA]">edit_square</span>
      </div>

      <div className="px-4 py-2 mt-2">
        <button
          onClick={onNewResearchClick}
          className="w-full flex items-center gap-2 px-3 py-2 bg-[#27272A] hover:bg-[#3F3F46] rounded-md transition-colors text-left text-[14px] font-medium"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          New Research
        </button>
      </div>

      <div className="flex-1 overflow-y-auto mt-2 px-2">
        {recentProjects.length > 0 && (
          <div className="mb-4">
            <h2 className="px-3 py-2 text-[11px] font-bold tracking-wider text-[#A1A1AA] uppercase">Recent</h2>
            <div className="flex flex-col gap-0.5">
              {recentProjects.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    if (onSelectProject) onSelectProject(p);
                    setIsOpenMobile(false);
                  }}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors text-left w-full outline-none truncate text-[13px] ${
                    activeTab === 'chat' && p.id === activeProjectId
                      ? 'bg-[#27272A] text-[#F4F4F5] font-medium'
                      : 'text-[#D4D4D8] hover:bg-[#27272A]'
                  }`}
                  title={p.title}
                >
                  <span className="truncate">{p.title}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Navigation Links */}
      <nav className="flex flex-col gap-0.5 p-2 mt-auto">
        {navItems.map((item) => {
          const isActive =
            item.id === 'library'
              ? activeTab === 'library' || activeTab === 'bibliography'
              : activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => handleTabClick(item.id)}
              className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-left w-full outline-none text-[13px] font-medium ${
                isActive
                  ? 'bg-[#27272A] text-[#F4F4F5]'
                  : 'text-[#D4D4D8] hover:bg-[#27272A]'
              }`}
            >
              <span
                className={`material-symbols-outlined text-[18px] ${
                  item.fillIcon || (isActive && item.id !== 'history') ? 'fill-1' : ''
                }`}
              >
                {item.icon}
              </span>
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Footer CTA */}
      <div className="p-4 pt-0">
        <button
          onClick={onUpgradeClick}
          className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-md bg-[#27272A] text-[#F4F4F5] hover:bg-[#3F3F46] transition-colors text-[13px] font-medium border border-[#3F3F46]"
        >
          <span className="material-symbols-outlined text-[16px]">upgrade</span>
          Upgrade Plan
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar Rail */}
      <aside className="bg-[#18181B] w-[260px] h-screen sticky left-0 top-0 border-r border-[#27272A] hidden md:flex flex-col shrink-0 z-20">
        {content}
      </aside>

      {/* Mobile Sidebar Overlay & Drawer */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsOpenMobile(false)}
          />
          <aside className="relative w-[260px] max-w-[80vw] h-full bg-[#18181B] border-r border-[#27272A] flex flex-col z-10 shadow-2xl">
            <button
              onClick={() => setIsOpenMobile(false)}
              className="absolute top-4 right-4 p-1 text-[#A1A1AA] hover:text-[#F4F4F5] rounded-full hover:bg-[#27272A]"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
            {content}
          </aside>
        </div>
      )}
    </>
  );
};
