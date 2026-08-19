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
        <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-on-primary font-headline-md">
          <span className="material-symbols-outlined text-[20px]">science</span>
        </div>
        <div>
          <h1 className="font-headline-md text-headline-md font-bold text-primary dark:text-primary-fixed leading-tight">Research Lab</h1>
          <p className="font-label-caps text-label-caps text-on-surface-variant uppercase">Academic Utility</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 flex flex-col gap-1">
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
              className={`flex items-center gap-3 px-3 py-2 rounded-DEFAULT transition-colors duration-200 text-left w-full outline-none focus:ring-2 focus:ring-primary ${
                isActive
                  ? 'text-primary dark:text-primary-fixed font-bold border-r-2 border-primary dark:border-primary-fixed bg-surface-variant/50'
                  : 'text-on-surface-variant dark:text-on-primary-container hover:bg-surface-variant dark:hover:bg-on-primary-fixed-variant'
              } ${item.id === 'settings' ? 'mt-auto' : ''}`}
            >
              <span
                className={`material-symbols-outlined text-[20px] ${
                  item.fillIcon || (isActive && item.id !== 'history') ? 'fill-1' : ''
                }`}
              >
                {item.icon}
              </span>
              <span className="font-body-md text-body-md truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer CTA */}
      <div className="mt-4 pt-4 border-t border-outline-variant">
        <button
          onClick={onUpgradeClick}
          className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-DEFAULT bg-primary text-on-primary hover:bg-slate-800 transition-colors font-body-md font-medium border border-primary cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">upgrade</span>
          Upgrade Plan
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar Rail */}
      <aside className="bg-surface-container-low dark:bg-primary-container w-sidebar-width h-screen sticky left-0 top-0 border-r border-outline-variant dark:border-outline hidden md:flex flex-col shrink-0 z-20">
        {content}
      </aside>

      {/* Mobile Sidebar Overlay & Drawer */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-xs"
            onClick={() => setIsOpenMobile(false)}
          />
          <aside className="relative w-sidebar-width max-w-[80vw] h-full bg-surface-container-low border-r border-outline-variant flex flex-col z-10 shadow-2xl">
            <button
              onClick={() => setIsOpenMobile(false)}
              className="absolute top-4 right-4 p-1 text-on-surface-variant hover:text-primary rounded-full hover:bg-black/5"
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
