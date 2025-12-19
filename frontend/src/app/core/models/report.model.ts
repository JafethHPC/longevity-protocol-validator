export interface Source {
  index: number;
  title: string;
  journal: string;
  year: number;
  pmid: string;
  abstract: string;
  url: string;
  citation_count: number;
  relevance_reason?: string;
}

export interface Finding {
  statement: string;
  source_indices: number[];
  confidence: 'high' | 'medium' | 'low';
}

export interface Protocol {
  name: string;
  species: string;
  dosage: string;
  frequency?: string;
  duration?: string;
  result: string;
  source_index: number;
}

export interface ResearchReport {
  id: string;
  question: string;
  generated_at: string;
  executive_summary: string;
  key_findings: Finding[];
  detailed_analysis: string;
  protocols: Protocol[];
  limitations: string;
  sources: Source[];
  total_papers_searched: number;
  papers_used: number;
}

export interface FollowUpMessage {
  question: string;
  answer: string;
}

export interface ReportRequest {
  question: string;
  max_sources?: number;
}

export interface FollowUpResponse {
  question: string;
  answer: string;
  report_id: string;
}

export type ReportStreamEventType =
  | 'progress'
  | 'report'
  | 'complete'
  | 'error';

export interface ReportStreamEvent {
  type: ReportStreamEventType;
  data: any;
}

export interface AppState {
  report: ResearchReport | null;
  isLoading: boolean;
  loadingMessage: string;
  followUpMessages: FollowUpMessage[];
  activeTab: 'findings' | 'protocols' | 'sources';
  expandedSources: Set<number>;
  error: string | null;
}
