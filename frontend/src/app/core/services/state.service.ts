import { Injectable, signal, computed } from '@angular/core';
import {
  ResearchReport,
  FollowUpMessage,
  ResearchProgress,
  ProgressStepId,
  ProgressEvent,
  createInitialProgress,
  PROGRESS_STEPS_CONFIG,
} from '../models';

/**
 * State management service for the application.
 * Uses Angular signals for reactive state management.
 */
@Injectable({
  providedIn: 'root',
})
export class StateService {
  // Core state signals
  private readonly _report = signal<ResearchReport | null>(null);
  private readonly _isLoading = signal<boolean>(false);
  private readonly _loadingMessage = signal<string>('');
  private readonly _followUpMessages = signal<FollowUpMessage[]>([]);
  private readonly _activeTab = signal<'findings' | 'protocols' | 'sources'>(
    'findings'
  );
  private readonly _expandedSources = signal<Set<number>>(new Set());
  private readonly _error = signal<string | null>(null);
  private readonly _isFollowUpLoading = signal<boolean>(false);

  // Progress state for streaming updates
  private readonly _progress = signal<ResearchProgress>(
    createInitialProgress()
  );

  // Public readonly signals
  readonly report = this._report.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly loadingMessage = this._loadingMessage.asReadonly();
  readonly followUpMessages = this._followUpMessages.asReadonly();
  readonly activeTab = this._activeTab.asReadonly();
  readonly expandedSources = this._expandedSources.asReadonly();
  readonly error = this._error.asReadonly();
  readonly isFollowUpLoading = this._isFollowUpLoading.asReadonly();
  readonly progress = this._progress.asReadonly();

  // Computed values
  readonly hasReport = computed(() => this._report() !== null);
  readonly sourcesCount = computed(() => this._report()?.sources?.length ?? 0);
  readonly findingsCount = computed(
    () => this._report()?.key_findings?.length ?? 0
  );
  readonly protocolsCount = computed(
    () => this._report()?.protocols?.length ?? 0
  );

  // Actions
  setReport(report: ResearchReport | null): void {
    this._report.set(report);
    if (report) {
      this._error.set(null);
      // Mark progress as complete
      this._progress.update((p) => ({
        ...p,
        isComplete: true,
        progressPercent: 100,
        steps: p.steps.map((s) => ({ ...s, status: 'complete' as const })),
      }));
    }
  }

  setLoading(isLoading: boolean, message: string = ''): void {
    this._isLoading.set(isLoading);
    this._loadingMessage.set(message);

    // Reset progress when starting a new load
    if (isLoading) {
      this._progress.set(createInitialProgress());
    }
  }

  /**
   * Update progress based on a progress event from the backend.
   */
  updateProgress(event: ProgressEvent): void {
    this._progress.update((current) => {
      // Find the index of the step that just updated
      const stepIndex = current.steps.findIndex((s) => s.id === event.step);

      if (stepIndex === -1) return current;

      // Update all steps
      const newSteps = current.steps.map((step, idx) => {
        if (idx < stepIndex) {
          // Previous steps are complete
          return { ...step, status: 'complete' as const };
        } else if (idx === stepIndex) {
          // Current step is active
          return {
            ...step,
            status: 'active' as const,
            detail: event.detail || undefined,
          };
        } else {
          // Future steps remain pending
          return { ...step, status: 'pending' as const };
        }
      });

      return {
        ...current,
        steps: newSteps,
        currentStepId: event.step,
        progressPercent: event.progress,
      };
    });

    // Also update the loading message
    this._loadingMessage.set(event.message);
  }

  /**
   * Mark progress as having an error.
   */
  setProgressError(errorMessage: string): void {
    this._progress.update((current) => ({
      ...current,
      hasError: true,
      errorMessage,
      steps: current.steps.map((s) =>
        s.status === 'active' ? { ...s, status: 'error' as const } : s
      ),
    }));
  }

  setActiveTab(tab: 'findings' | 'protocols' | 'sources'): void {
    this._activeTab.set(tab);
  }

  toggleSourceExpanded(index: number): void {
    const current = new Set(this._expandedSources());
    if (current.has(index)) {
      current.delete(index);
    } else {
      current.add(index);
    }
    this._expandedSources.set(current);
  }

  isSourceExpanded(index: number): boolean {
    return this._expandedSources().has(index);
  }

  addFollowUpMessage(question: string, answer: string): void {
    this._followUpMessages.update((messages) => [
      ...messages,
      { question, answer },
    ]);
  }

  setFollowUpLoading(isLoading: boolean): void {
    this._isFollowUpLoading.set(isLoading);
  }

  setError(error: string | null): void {
    this._error.set(error);
  }

  resetState(): void {
    this._report.set(null);
    this._followUpMessages.set([]);
    this._expandedSources.set(new Set());
    this._activeTab.set('findings');
    this._error.set(null);
    this._isLoading.set(false);
    this._progress.set(createInitialProgress());
  }
}
