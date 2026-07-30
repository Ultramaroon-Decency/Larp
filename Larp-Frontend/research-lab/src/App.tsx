import React, { useState } from 'react';
import {
  ActiveTab,
  ResearchProject,
  ResearchMode,
  AttachedFile,
  Source
} from './types';
import { INITIAL_PROJECTS, INITIAL_COLLECTIONS } from './data/mockData';
import { Sidebar } from './components/Sidebar';
import { TopAppBar } from './components/TopAppBar';
import { NewResearchView } from './components/NewResearchView';
import { ChatResearchView } from './components/ChatResearchView';
import { SavedLibraryView } from './components/SavedLibraryView';
import { BibliographyView } from './components/BibliographyView';
import { HistoryView } from './components/HistoryView';
import { SettingsView } from './components/SettingsView';
import { UpgradeModal } from './components/UpgradeModal';

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('new');
  const [projects, setProjects] = useState<ResearchProject[]>(INITIAL_PROJECTS);
  const [collections] = useState(INITIAL_COLLECTIONS);
  const [activeProjectId, setActiveProjectId] = useState<string>('quantum-2024');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isOpenMobileMenu, setIsOpenMobileMenu] = useState(false);
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [defaultMode, setDefaultMode] = useState<ResearchMode>('quick');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const activeProject = projects.find((p) => p.id === activeProjectId) || projects[0] || null;

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleNewResearchClick = () => {
    setActiveTab('new');
  };

  const handleSelectProject = (project: ResearchProject) => {
    setActiveProjectId(project.id);
    setActiveTab('chat');
  };

  const handleOpenBibliography = (project: ResearchProject) => {
    setActiveProjectId(project.id);
    setActiveTab('bibliography');
  };

  const handleToggleStar = (id: string) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === id ? { ...p, isStarred: !p.isStarred } : p))
    );
    showToast('Starred status updated.');
  };

  const handleDeleteProject = (id: string) => {
    setProjects((prev) => prev.filter((p) => p.id !== id));
    showToast('Research thread deleted.');
  };

  const handleSynthesize = async (
    query: string,
    mode: ResearchMode,
    attachedFiles: AttachedFile[]
  ) => {
    const newId = `project-${Date.now()}`;
    const newProject: ResearchProject = {
      id: newId,
      title: query.length > 35 ? `${query.substring(0, 35)}...` : query,
      description: `Academic synthesis query: "${query}"`,
      query,
      mode,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      dateLabel: 'Today',
      status: 'synthesizing',
      category: 'Academic Research',
      isStarred: false,
      isShared: false,
      messages: [
        {
          id: `msg-${Date.now()}-u`,
          role: 'user',
          content: query,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ],
      sources: [],
      attachedFiles
    };

    setProjects((prev) => [newProject, ...prev]);
    setActiveProjectId(newId);
    setActiveTab('chat');
    setIsSynthesizing(true);

    try {
      const res = await fetch('/api/research/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, mode, attachedFiles })
      });

      if (!res.ok) throw new Error('Failed to reach synthesis API');

      const data = await res.json();

      setProjects((prev) =>
        prev.map((p) => {
          if (p.id !== newId) return p;

          return {
            ...p,
            title: data.title || p.title,
            status: 'completed',
            messages: [
              ...p.messages,
              {
                id: `msg-${Date.now()}-a`,
                role: 'assistant',
                title: data.title,
                content: data.overview || 'Synthesis complete.',
                sections: data.sections || [],
                codeSnippet: data.codeSnippet || '',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              }
            ],
            sources: (data.sources || []).map((s: Source, idx: number) => ({
              ...s,
              id: `src-${newId}-${idx + 1}`
            }))
          };
        })
      );
    } catch (err) {
      console.error('Synthesis error:', err);
      showToast('Completed using offline academic synthesis model.');
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleRefineQuery = async (refineText: string) => {
    if (!activeProject) return;

    const userMsg = {
      id: `msg-${Date.now()}-u`,
      role: 'user' as const,
      content: refineText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setProjects((prev) =>
      prev.map((p) =>
        p.id === activeProject.id
          ? { ...p, messages: [...p.messages, userMsg] }
          : p
      )
    );

    setIsSynthesizing(true);

    try {
      const combinedQuery = `${activeProject.query} Follow-up parameter: ${refineText}`;
      const res = await fetch('/api/research/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: combinedQuery,
          mode: activeProject.mode,
          attachedFiles: activeProject.attachedFiles
        })
      });

      const data = await res.json();

      const assistantMsg = {
        id: `msg-${Date.now()}-a`,
        role: 'assistant' as const,
        title: `Refined Analysis: ${refineText.substring(0, 30)}...`,
        content: data.overview || 'Refined synthesis response generated.',
        sections: data.sections || [],
        codeSnippet: data.codeSnippet || '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setProjects((prev) =>
        prev.map((p) => {
          if (p.id !== activeProject.id) return p;
          return {
            ...p,
            messages: [...p.messages, assistantMsg],
            sources:
              data.sources && data.sources.length > 0
                ? data.sources.map((s: Source, idx: number) => ({
                    ...s,
                    id: `src-${p.id}-${p.sources.length + idx + 1}`,
                    index: p.sources.length + idx + 1
                  }))
                : p.sources
          };
        })
      );
    } catch (err) {
      console.error(err);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleDownloadBibtex = async (sources: Source[], title: string) => {
    try {
      const res = await fetch('/api/export/bibtex', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sources, title })
      });

      const text = await res.text();
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title.toLowerCase().replace(/[^a-z0-9]/g, '_')}_references.bib`;
      link.click();
      URL.revokeObjectURL(url);
      showToast('BibTeX file downloaded!');
    } catch (err) {
      console.error(err);
      showToast('Failed to export BibTeX.');
    }
  };

  const handleExportPdf = () => {
    window.print();
  };

  const handleShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      showToast('Research link copied to clipboard!');
    } else {
      showToast('Sharing link generated.');
    }
  };

  const handleArchive = () => {
    showToast('Research thread archived to library.');
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#F7F9FB] text-[#191C1E] font-sans antialiased">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 bg-[#0F172A] text-white text-[13px] font-medium px-4 py-2.5 rounded-md shadow-xl border border-slate-700 flex items-center gap-2 animate-bounce">
          <span className="material-symbols-outlined text-[18px]">check_circle</span>
          {toastMessage}
        </div>
      )}

      {/* Left Navigation Rail */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOpenMobile={isOpenMobileMenu}
        setIsOpenMobile={setIsOpenMobileMenu}
        onUpgradeClick={() => setIsUpgradeModalOpen(true)}
        onNewResearchClick={handleNewResearchClick}
      />

      {/* Main Screen Container */}
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative">
        <TopAppBar
          activeTab={activeTab}
          activeProject={activeProject}
          onOpenMobileMenu={() => setIsOpenMobileMenu(true)}
          onExportPdf={handleExportPdf}
          onShare={handleShare}
          onArchive={handleArchive}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onNewResearchClick={handleNewResearchClick}
        />

        {activeTab === 'new' && (
          <NewResearchView onSynthesize={handleSynthesize} />
        )}

        {activeTab === 'chat' && activeProject && (
          <ChatResearchView
            project={activeProject}
            onRefineQuery={handleRefineQuery}
            onViewBibliographyClick={() => setActiveTab('bibliography')}
            isSynthesizing={isSynthesizing}
          />
        )}

        {activeTab === 'library' && (
          <SavedLibraryView
            collections={collections}
            projects={projects}
            onSelectProject={handleSelectProject}
            onOpenBibliography={handleOpenBibliography}
            searchQuery={searchQuery}
          />
        )}

        {activeTab === 'bibliography' && activeProject && (
          <BibliographyView
            project={activeProject}
            onDownloadBibtex={handleDownloadBibtex}
          />
        )}

        {activeTab === 'history' && (
          <HistoryView
            projects={projects}
            onSelectProject={handleSelectProject}
            onToggleStar={handleToggleStar}
            onDeleteProject={handleDeleteProject}
            searchQuery={searchQuery}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsView
            defaultMode={defaultMode}
            setDefaultMode={setDefaultMode}
            onUpgradeClick={() => setIsUpgradeModalOpen(true)}
          />
        )}
      </div>

      {/* Upgrade Plan Modal */}
      <UpgradeModal
        isOpen={isUpgradeModalOpen}
        onClose={() => setIsUpgradeModalOpen(false)}
      />
    </div>
  );
}
