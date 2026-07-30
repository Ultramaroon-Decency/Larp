export type ResearchMode = 'quick' | 'deep';

export type PipelineStepStatus = 'pending' | 'running' | 'done' | 'error';

/** One step in the 5-stage research pipeline. */
export interface PipelineStep {
  id: string;
  name: string;
  description: string;
  api: string;
  status: PipelineStepStatus;
  cost?: string;
  duration?: number;
  error?: string;
}

/** x402 payment receipt emitted per API call in the pipeline. */
export interface PaymentReceipt {
  stepId: string;
  stepName: string;
  amount: string;      // e.g. "0.0025" USDC
  currency: string;
  network: string;
  txHash: string;
  from: string;        // agent wallet
  payTo: string;       // API provider wallet
  timestamp: string;
}

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
  /** Pipeline steps recorded after synthesis (shows what the agent did). */
  pipelineSteps?: PipelineStep[];
  /** x402 payment receipts from this research session. */
  payments?: PaymentReceipt[];
  /** Total USDC cost of this research (e.g. "0.0091"). */
  totalCost?: string;
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
