export type ResearchMode = 'quick' | 'deep';

export interface Source {
  id: string;
  index: number;
  title: string;
  authors: string;
  year: number;
  journal: string;
  relevance: number; // 0 to 1 e.g. 0.98
  doi: string;
  url?: string;
  tags: string[];
  abstract?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  title?: string;
  sections?: {
    heading: string;
    body: string;
    bulletPoints?: string[];
  }[];
  codeSnippet?: string;
  citations?: number[];
}

export interface AttachedFile {
  id: string;
  name: string;
  size: string;
  type: string;
}

export interface ResearchProject {
  id: string;
  title: string;
  description: string;
  query: string;
  mode: ResearchMode;
  createdAt: string;
  updatedAt: string;
  dateLabel: string;
  status: 'draft' | 'completed' | 'synthesizing';
  category: string;
  isStarred: boolean;
  isShared: boolean;
  messages: ChatMessage[];
  sources: Source[];
  attachedFiles: AttachedFile[];
}

export interface Collection {
  id: string;
  title: string;
  refsCount: number;
  updatedAgo: string;
  icon: string;
  category: string;
  projectIds: string[];
}

export type ActiveTab = 'new' | 'chat' | 'history' | 'library' | 'bibliography' | 'settings';
