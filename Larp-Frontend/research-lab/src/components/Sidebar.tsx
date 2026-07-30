import React from 'react';
import { ActiveTab } from '../types';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  isOpenMobile: boolean;
  setIsOpenMobile: (open: boolean) => void;
  onUpgradeClick: () => void;
  onNewResearchClick: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isOpenMobile,
  setIsOpenMobile,
  onUpgradeClick,
  onNewResearchClick
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
    { id: 'new', label: 'New Research', icon: 'add_circle' },
    { id: 'history', label: 'History', icon: 'history' },
    { id: 'library', label: 'Saved Library', icon: 'book', fillIcon: activeTab === 'library' || activeTab === 'bibliography' },
    { id: 'settings', label: 'Settings', icon: 'settings' }
  ];

  const content = (
    <div className="flex flex-col h-full p-4">
      {/* Header */}
      <div className="mb-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-[#0F172A] flex items-center justify-center text-white shrink-0 shadow-sm">
          <span className="material-symbols-outlined text-[20px]">science</span>
        </div>
        <div>
          <h1 className="font-bold text-[20px] leading-tight text-[#0F172A] dark:text-white">Research Lab</h1>
          <p className="text-[11px] font-bold tracking-wider text-[#45464D] uppercase">Academic Utility</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 flex flex-col gap-1.5">
        {navItems.map((item) => {
          const isActive =
            item.id === 'new'
              ? activeTab === 'new'
              : item.id === 'library'
              ? activeTab === 'library' || activeTab === 'bibliography'
              : activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => handleTabClick(item.id)}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-md text-[15px] transition-colors duration-200 text-left w-full outline-none focus:ring-2 focus:ring-[#0F172A] ${
                isActive
                  ? 'bg-[#E0E3E5] font-bold text-[#0F172A] border-r-2 border-[#0F172A]'
                  : 'text-[#45464D] hover:bg-[#E0E3E5]/60 hover:text-[#0F172A]'
              }`}
            >
              <span
                className={`material-symbols-outlined shrink-0 text-[20px] ${
                  item.fillIcon || (isActive && item.id !== 'history') ? 'fill-1' : ''
                }`}
              >
                {item.icon}
              </span>
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer CTA */}
      <div className="mt-auto pt-4 border-t border-[#C6C6CD]/50">
        <button
          onClick={onUpgradeClick}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-md bg-[#0F172A] text-white hover:bg-slate-800 transition-colors font-medium text-[13px] tracking-wide uppercase border border-[#0F172A] shadow-sm cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">bolt</span>
          Upgrade Plan
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar Rail */}
      <aside className="w-[280px] h-screen sticky left-0 top-0 bg-[#F2F4F6] border-r border-[#C6C6CD] hidden md:flex flex-col shrink-0 z-20">
        {content}
      </aside>

      {/* Mobile Sidebar Overlay & Drawer */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-xs"
            onClick={() => setIsOpenMobile(false)}
          />
          <aside className="relative w-[280px] max-w-[80vw] h-full bg-[#F2F4F6] border-r border-[#C6C6CD] flex flex-col z-10 shadow-2xl">
            <button
              onClick={() => setIsOpenMobile(false)}
              className="absolute top-4 right-4 p-1 text-[#45464D] hover:text-[#0F172A] rounded-full hover:bg-black/5"
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
