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
  templateUrl: './report-page.component.html',
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
