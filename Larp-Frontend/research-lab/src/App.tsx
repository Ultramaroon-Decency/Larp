import React, { useState, useRef, useEffect } from 'react';
import {
  ActiveTab,
  ResearchProject,
  ResearchMode,
  AttachedFile,
  Source,
  PipelineStep,
  PaymentReceipt,
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
  // Live pipeline state — updated via SSE as steps run
  const [livePipelineSteps, setLivePipelineSteps] = useState<PipelineStep[]>([]);
  const [livePayments, setLivePayments] = useState<PaymentReceipt[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const activeProject = projects.find((p) => p.id === activeProjectId) || projects[0] || null;

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

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
    setLivePipelineSteps([]);
    setLivePayments([]);

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      const token = localStorage.getItem('access_token') || '';
      
      const res = await fetch('/api/v1/research/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ query, depth: mode, title: query })
      });

      if (res.status === 401) {
          showToast('Authentication required for deep research mode.');
          setIsSynthesizing(false);
          setProjects((prev) => prev.filter(p => p.id !== newId));
          return;
      }
      
      if (!res.ok) throw new Error('Failed to start research job');

      const data = await res.json();
      const jobId = data.data?.id;
      if (!jobId) throw new Error('No Job ID returned');

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws/research/${jobId}${token ? `?token=${token}` : ''}`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = async (event) => {
        try {
          const wsData = JSON.parse(event.data);
          
          if (wsData.event === 'job_progress_updated') {
            const agentName = wsData.current_agent || 'Unknown';
            const step: PipelineStep = {
              id: agentName,
              name: agentName,
              status: wsData.status === 'in_progress' ? 'running' : wsData.status === 'completed' ? 'done' : 'error',
              latency: wsData.execution_time_ms ? `${wsData.execution_time_ms}ms` : undefined,
            };

            setLivePipelineSteps((prev) => {
              const agentOrder = ['PlannerAgent', 'SearchAgent', 'FactCheckerAgent', 'CitationAgent', 'ReportAgent'];
              const currentIndex = agentOrder.indexOf(agentName);

              if (wsData.status === 'completed' || wsData.progress_percentage === 100) {
                // Mark all accumulated steps as done
                return prev.map((s) => ({ ...s, status: 'done' as const }));
              }

              let updated = prev.map((s) => {
                const stepIndex = agentOrder.indexOf(s.id);
                if (stepIndex !== -1 && currentIndex !== -1 && stepIndex < currentIndex) {
                  return { ...s, status: 'done' as const };
                }
                if (s.id === step.id) {
                  return step;
                }
                return s;
              });

              if (!updated.some((s) => s.id === step.id)) {
                updated.push(step);
              }
              return updated;
            });

            if (wsData.progress_percentage === 100) {
                ws.close();
                wsRef.current = null;
                
                // Extract report directly from WebSocket event (works for anonymous users)
                const reportData = wsData.report || {};
                const sourcesData = wsData.sources || [];
                
                // If report is in the WebSocket event, use it directly
                if (reportData.content_markdown) {
                    setProjects((prev) =>
                      prev.map((p) => {
                        if (p.id !== newId) return p;
                        return {
                          ...p,
                          title: reportData.title || p.title,
                          status: 'completed',
                          messages: [
                            ...p.messages,
                            {
                              id: `msg-${Date.now()}-a`,
                              role: 'assistant',
                              title: reportData.title,
                              content: reportData.content_markdown,
                              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                            }
                          ],
                          sources: sourcesData.map((s: any, idx: number) => ({
                            id: `src-${idx}`,
                            title: s.title,
                            url: s.url,
                            snippet: s.snippet,
                            relevanceScore: s.relevance_score
                          }))
                        };
                      })
                    );
                } else if (token) {
                    // Authenticated users: fallback to GET endpoint  
                    try {
                        const reportRes = await fetch(`/api/v1/research/${jobId}`, {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        if (reportRes.ok) {
                            const finalData = await reportRes.json();
                            const dbReport = finalData.data?.report || {};
                            const dbSources = finalData.data?.sources || [];
                            setProjects((prev) =>
                              prev.map((p) => {
                                if (p.id !== newId) return p;
                                return {
                                  ...p,
                                  title: finalData.data?.title || p.title,
                                  status: 'completed',
                                  messages: [
                                    ...p.messages,
                                    {
                                      id: `msg-${Date.now()}-a`,
                                      role: 'assistant',
                                      title: finalData.data?.title,
                                      content: dbReport.content_markdown || 'Synthesis complete.',
                                      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                    }
                                  ],
                                  sources: dbSources.map((s: any) => ({
                                    id: s.id,
                                    title: s.title,
                                    url: s.url,
                                    snippet: s.snippet,
                                    relevanceScore: s.relevance_score
                                  }))
                                };
                              })
                            );
                        }
                    } catch {
                        // Silently fail on report fetch
                    }
                } else {
                    // Mark as completed even without report data
                    setProjects((prev) =>
                      prev.map((p) => p.id === newId ? { ...p, status: 'completed' } : p)
                    );
                }
                setIsSynthesizing(false);
            }
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onerror = () => {
        ws.close();
        wsRef.current = null;
        setIsSynthesizing(false);
      };

    } catch (err) {
      console.error('Synthesis error:', err);
      showToast('Synthesis failed. Please try again.');
      setProjects((prev) =>
        prev.map((p) => (p.id === newId ? { ...p, status: 'failed' } : p))
      );
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
      const res = await fetch('/api/v1/research/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: combinedQuery,
          depth: activeProject.mode, // FastAPI expects 'depth'
          attachedFiles: activeProject.attachedFiles
        })
      });

      if (!res.ok) throw new Error('Refinement request failed');

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
      showToast('Refinement failed. Please try again.');
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
    <div className="flex h-screen overflow-hidden bg-background text-on-background font-body-md text-body-md antialiased selection:bg-primary selection:text-on-primary">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 bg-[#0F172A] text-white text-[13px] font-medium px-4 py-2.5 rounded-md shadow-xl border border-slate-700 flex items-center gap-2 animate-fade-in-down">
          <span className="material-symbols-outlined text-[18px] text-emerald-400">check_circle</span>
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
            livePipelineSteps={livePipelineSteps}
            livePayments={livePayments}
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
            livePayments={livePayments}
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
