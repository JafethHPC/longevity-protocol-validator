/**
 * Progress Models
 *
 * TypeScript interfaces for streaming progress updates
 * during report generation.
 */

/**
 * All possible step identifiers in the research pipeline.
 * Must match backend ProgressStep enum values.
 */
export type ProgressStepId =
  | 'optimizing'
  | 'searching_pubmed'
  | 'searching_openalex'
  | 'searching_europepmc'
  | 'searching_crossref'
  | 'concept_search'
  | 'deduplicating'
  | 'ranking'
  | 'filtering'
  | 'generating_findings'
  | 'extracting_protocols'
  | 'complete';

/**
 * Status of a progress step.
 */
export type ProgressStepStatus = 'pending' | 'active' | 'complete' | 'error';

/**
 * Configuration for a single progress step.
 */
export interface ProgressStepConfig {
  id: ProgressStepId;
  label: string;
  order: number;
}

/**
 * Runtime state of a progress step.
 */
export interface ProgressStep {
  id: ProgressStepId;
  label: string;
  status: ProgressStepStatus;
  detail?: string;
}

/**
 * Complete research progress state.
 */
export interface ResearchProgress {
  steps: ProgressStep[];
  currentStepId: ProgressStepId | null;
  progressPercent: number;
  isComplete: boolean;
  hasError: boolean;
  errorMessage?: string;
}

/**
 * Progress event received from backend SSE stream.
 */
export interface ProgressEvent {
  step: ProgressStepId;
  message: string;
  detail: string | null;
  progress: number;
}

/**
 * Default step configuration with labels and order.
 * Matches backend STEP_CONFIG.
 */
export const PROGRESS_STEPS_CONFIG: ProgressStepConfig[] = [
  { id: 'optimizing', label: 'Optimizing search queries', order: 1 },
  { id: 'searching_pubmed', label: 'Searching PubMed', order: 2 },
  { id: 'searching_openalex', label: 'Searching OpenAlex', order: 3 },
  { id: 'searching_europepmc', label: 'Searching Europe PMC', order: 4 },
  { id: 'searching_crossref', label: 'Searching CrossRef', order: 5 },
  { id: 'concept_search', label: 'Running concept searches', order: 6 },
  { id: 'deduplicating', label: 'Removing duplicates', order: 7 },
  { id: 'ranking', label: 'Ranking by relevance', order: 8 },
  { id: 'filtering', label: 'Filtering with AI', order: 9 },
  { id: 'generating_findings', label: 'Generating findings', order: 10 },
  { id: 'extracting_protocols', label: 'Extracting protocols', order: 11 },
];

/**
 * Create initial progress state with all steps pending.
 */
export function createInitialProgress(): ResearchProgress {
  return {
    steps: PROGRESS_STEPS_CONFIG.map((config) => ({
      id: config.id,
      label: config.label,
      status: 'pending' as ProgressStepStatus,
    })),
    currentStepId: null,
    progressPercent: 0,
    isComplete: false,
    hasError: false,
  };
}
