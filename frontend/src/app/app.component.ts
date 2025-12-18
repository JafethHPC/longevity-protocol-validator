import { Component, inject, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ReportService,
  ResearchReport,
  ReportStreamEvent,
  Source,
  Finding,
  Protocol,
} from './services/report.service';
import { MarkdownPipe } from './pipes/markdown.pipe';

interface FollowUpMessage {
  question: string;
  answer: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownPipe],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  @ViewChild('reportContainer') private reportContainer!: ElementRef;

  reportService = inject(ReportService);

  // UI State
  currentInput = '';
  isLoading = false;
  currentStatus = '';
  activeTab: 'findings' | 'protocols' | 'sources' = 'findings';

  // Report data
  report: ResearchReport | null = null;
  followUpMessages: FollowUpMessage[] = [];
  followUpInput = '';
  isFollowUpLoading = false;

  // Source expansion tracking
  expandedSources: Set<number> = new Set();

  generateReport() {
    if (!this.currentInput.trim()) return;

    const question = this.currentInput;
    this.currentInput = '';
    this.isLoading = true;
    this.currentStatus = 'Searching scientific databases...';
    this.report = null;
    this.followUpMessages = [];

    const stream = this.reportService.generateReport(question);

    stream.subscribe({
      next: (event: ReportStreamEvent) => {
        switch (event.type) {
          case 'status':
            this.currentStatus = event.data.message;
            break;

          case 'report':
            this.report = event.data;
            this.currentStatus = 'Report generated!';
            break;

          case 'complete':
            this.isLoading = false;
            this.currentStatus = '';
            break;

          case 'error':
            this.isLoading = false;
            this.currentStatus = `Error: ${event.data.message}`;
            break;
        }
      },
      error: (err) => {
        this.isLoading = false;
        this.currentStatus = 'An error occurred while generating the report.';
        console.error('Report generation error:', err);
      },
      complete: () => {
        this.isLoading = false;
      },
    });
  }

  askFollowUp() {
    if (!this.followUpInput.trim() || !this.report) return;

    const question = this.followUpInput;
    this.followUpInput = '';
    this.isFollowUpLoading = true;

    this.reportService.askFollowUp(question).subscribe({
      next: (response) => {
        this.followUpMessages.push({
          question: response.question,
          answer: response.answer,
        });
        this.isFollowUpLoading = false;
      },
      error: (err) => {
        this.followUpMessages.push({
          question: question,
          answer: 'Error: Could not process follow-up question.',
        });
        this.isFollowUpLoading = false;
        console.error('Follow-up error:', err);
      },
    });
  }

  newReport() {
    this.report = null;
    this.followUpMessages = [];
    this.expandedSources = new Set();
    this.reportService.resetReport();
  }

  toggleSource(index: number) {
    if (this.expandedSources.has(index)) {
      this.expandedSources.delete(index);
    } else {
      this.expandedSources.add(index);
    }
  }

  isSourceExpanded(index: number): boolean {
    return this.expandedSources.has(index);
  }

  getConfidenceColor(confidence: string): string {
    switch (confidence.toLowerCase()) {
      case 'high':
        return 'text-emerald-600';
      case 'medium':
        return 'text-amber-600';
      case 'low':
        return 'text-red-600';
      default:
        return 'text-stone-600';
    }
  }

  getConfidenceBadge(confidence: string): string {
    switch (confidence.toLowerCase()) {
      case 'high':
        return 'bg-emerald-100 text-emerald-800';
      case 'medium':
        return 'bg-amber-100 text-amber-800';
      case 'low':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-stone-100 text-stone-800';
    }
  }

  formatSourceIndices(indices: number[]): string {
    return indices.map((i) => `[${i}]`).join(' ');
  }

  exportPdf() {
    this.reportService.exportPdf();
  }
}
