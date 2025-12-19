/**
 * Core data models for the Research Report application.
 * These interfaces define the structure of data exchanged with the backend API.
 */

// Source reference from a scientific paper
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

// A key finding from the research analysis
export interface Finding {
  statement: string;
  source_indices: number[];
  confidence: 'high' | 'medium' | 'low';
}

// An extracted protocol/intervention from papers
export interface Protocol {
  name: string;
  species: string;
  dosage: string;
  frequency?: string;
  duration?: string;
  result: string;
  source_index: number;
}

// Complete research report structure
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

// Follow-up question and answer
export interface FollowUpMessage {
  question: string;
  answer: string;
}

// Request to generate a new report
export interface ReportRequest {
  question: string;
  max_sources?: number;
}

// Response from follow-up question
export interface FollowUpResponse {
  question: string;
  answer: string;
  report_id: string;
}

// Stream event types for report generation
export type ReportStreamEventType =
  | 'progress'
  | 'report'
  | 'complete'
  | 'error';

export interface ReportStreamEvent {
  type: ReportStreamEventType;
  data: any;
}

// Application state
export interface AppState {
  report: ResearchReport | null;
  isLoading: boolean;
  loadingMessage: string;
  followUpMessages: FollowUpMessage[];
  activeTab: 'findings' | 'protocols' | 'sources';
  expandedSources: Set<number>;
  error: string | null;
}
