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
  source_type?: 'paper' | 'clinical_trial'; // New field to distinguish clinical trials
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

/**
 * Configuration for a specific data source.
 */
export interface SourceConfig {
  enabled: boolean;
  max_results: number;
}

/**
 * Full research configuration - controls all aspects of the retrieval pipeline.
 * All fields have sensible defaults, so you only need to specify what you want to change.
 */
export interface ResearchConfig {
  // Output limits
  max_sources: number; // Default: 15, Max total sources in report
  min_clinical_trials: number; // Default: 3, Minimum clinical trials to include
  min_papers: number; // Default: 5, Minimum papers to include

  // Source configurations
  pubmed_enabled: boolean; // Default: true
  pubmed_max_results: number; // Default: 100

  openalex_enabled: boolean; // Default: true
  openalex_max_results: number; // Default: 100

  europe_pmc_enabled: boolean; // Default: true
  europe_pmc_max_results: number; // Default: 100

  crossref_enabled: boolean; // Default: true
  crossref_max_results: number; // Default: 100

  clinical_trials_enabled: boolean; // Default: true
  clinical_trials_max_results: number; // Default: 25

  // Processing options
  clinical_trial_boost: number; // Default: 0.15, Boost for clinical trials in ranking
  include_fulltext: boolean; // Default: true, Whether to fetch full text
}

/**
 * Default research configuration values.
 */
export const DEFAULT_RESEARCH_CONFIG: ResearchConfig = {
  max_sources: 15,
  min_clinical_trials: 3,
  min_papers: 5,

  pubmed_enabled: true,
  pubmed_max_results: 100,

  openalex_enabled: true,
  openalex_max_results: 100,

  europe_pmc_enabled: true,
  europe_pmc_max_results: 100,

  crossref_enabled: true,
  crossref_max_results: 100,

  clinical_trials_enabled: true,
  clinical_trials_max_results: 25,

  clinical_trial_boost: 0.15,
  include_fulltext: true,
};

/**
 * Request to generate a research report with full configuration control.
 */
export interface ReportRequest extends Partial<ResearchConfig> {
  question: string;
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
