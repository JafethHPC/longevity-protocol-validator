import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReportService, StateService } from '../../core/services';
import {
  TabBarComponent,
  Tab,
  TabId,
} from '../../shared/components/tab-bar/tab-bar.component';
import {
  SearchInputComponent,
  ResearchProgressComponent,
  ReportHeaderComponent,
  FindingsTabComponent,
  ProtocolsTabComponent,
  SourcesTabComponent,
  FollowUpSectionComponent,
} from './components';

@Component({
  selector: 'app-report-page',
  standalone: true,
  imports: [
    CommonModule,
    TabBarComponent,
    SearchInputComponent,
    ResearchProgressComponent,
    ReportHeaderComponent,
    FindingsTabComponent,
    ProtocolsTabComponent,
    SourcesTabComponent,
    FollowUpSectionComponent,
  ],
  template: `
    <div class="min-h-screen bg-stone-100 flex flex-col">
      <!-- Header -->
      <header
        class="bg-white border-b border-stone-200 py-4 px-6 flex items-center justify-between shadow-sm"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-md"
          >
            <svg
              class="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-bold text-stone-800">
              Research Report Generator
            </h1>
            <p class="text-sm text-stone-500">
              AI-powered scientific literature analysis
            </p>
          </div>
        </div>

        <div *ngIf="state.hasReport()" class="flex items-center gap-2">
          <button
            (click)="exportPdf()"
            class="px-4 py-2 text-sm font-medium text-stone-600 hover:text-stone-700 hover:bg-stone-100 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Export PDF
          </button>
          <button
            (click)="newReport()"
            class="px-4 py-2 text-sm font-medium text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors"
          >
            + New Report
          </button>
        </div>
      </header>

      <!-- Main Content -->
      <main class="flex-1 overflow-auto p-6">
        <!-- Search Input (no report, not loading) -->
        <app-search-input
          *ngIf="!state.hasReport() && !state.isLoading()"
          (search)="generateReport($event)"
        />

        <!-- Loading State with Progress -->
        <app-research-progress
          *ngIf="state.isLoading()"
          [progress]="state.progress()"
        />

        <!-- Report Display -->
        <div
          *ngIf="state.hasReport() && !state.isLoading()"
          class="max-w-4xl mx-auto"
        >
          <app-report-header [report]="state.report()!" />

          <!-- Tabs -->
          <app-tab-bar
            [tabs]="tabs()"
            [activeTab]="state.activeTab()"
            (tabChange)="state.setActiveTab($event)"
          />

          <div class="mt-6">
            <!-- Findings Tab -->
            <app-findings-tab
              *ngIf="state.activeTab() === 'findings'"
              [report]="state.report()!"
            />

            <!-- Protocols Tab -->
            <app-protocols-tab
              *ngIf="state.activeTab() === 'protocols'"
              [report]="state.report()!"
            />

            <!-- Sources Tab -->
            <app-sources-tab
              *ngIf="state.activeTab() === 'sources'"
              [report]="state.report()!"
              [expandedSources]="state.expandedSources()"
              (toggleSourceExpanded)="state.toggleSourceExpanded($event)"
            />
          </div>

          <!-- Follow-up Section -->
          <app-follow-up-section
            [messages]="state.followUpMessages()"
            [isLoading]="state.isFollowUpLoading()"
            (askQuestion)="askFollowUp($event)"
          />
        </div>
      </main>
    </div>
  `,
})
export class ReportPageComponent {
  private readonly reportService = inject(ReportService);
  readonly state = inject(StateService);

  // Computed tabs with counts
  readonly tabs = computed<Tab[]>(() => {
    const report = this.state.report();
    return [
      {
        id: 'findings' as TabId,
        label: 'Key Findings',
        count: report?.key_findings?.length ?? 0,
      },
      {
        id: 'protocols' as TabId,
        label: 'Protocols',
        count: report?.protocols?.length ?? 0,
      },
      {
        id: 'sources' as TabId,
        label: 'Sources',
        count: report?.sources?.length ?? 0,
      },
    ];
  });

  generateReport(question: string): void {
    this.state.setLoading(true, 'Initializing research...');
    this.reportService.resetReport();

    this.reportService.generateReport(question).subscribe({
      next: (event) => {
        if (event.type === 'progress') {
          // Update progress state with granular step info
          this.state.updateProgress(event.data);
        } else if (event.type === 'report') {
          this.state.setReport(event.data);
          this.state.setLoading(false);
        } else if (event.type === 'error') {
          this.state.setError(event.data.message || event.data.error);
          this.state.setProgressError(event.data.message || event.data.error);
          this.state.setLoading(false);
        }
      },
      error: (err) => {
        this.state.setError(err.message);
        this.state.setProgressError(err.message);
        this.state.setLoading(false);
      },
    });
  }

  askFollowUp(question: string): void {
    this.state.setFollowUpLoading(true);

    this.reportService.askFollowUp(question).subscribe({
      next: (response) => {
        this.state.addFollowUpMessage(response.question, response.answer);
        this.state.setFollowUpLoading(false);
      },
      error: (err) => {
        this.state.addFollowUpMessage(
          question,
          'Error: Could not process follow-up question.'
        );
        this.state.setFollowUpLoading(false);
      },
    });
  }

  exportPdf(): void {
    this.reportService.exportPdf();
  }

  newReport(): void {
    this.state.resetState();
    this.reportService.resetReport();
  }
}
