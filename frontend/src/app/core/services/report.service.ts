import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ResearchReport, ReportStreamEvent, FollowUpResponse } from '../models';

/**
 * Service for interacting with the Research Report API.
 * Handles report generation, retrieval, follow-ups, and PDF export.
 */
@Injectable({
  providedIn: 'root',
})
export class ReportService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;
  private currentReportId: string | null = null;

  /**
   * Generate a new research report with streaming progress updates.
   */
  generateReport(
    question: string,
    maxSources: number = 10
  ): Subject<ReportStreamEvent> {
    const subject = new Subject<ReportStreamEvent>();
    const url = `${this.apiUrl}/api/reports/generate/stream`;

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        max_sources: maxSources,
      }),
    })
      .then(async (response) => {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          subject.next({
            type: 'error',
            data: { message: 'No response body' },
          });
          subject.complete();
          return;
        }

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const chunk of lines) {
            if (!chunk.trim()) continue;

            const eventMatch = chunk.match(/event: (\w+)/);
            const dataMatch = chunk.match(/data: (.+)/s);

            if (eventMatch && dataMatch) {
              const eventType = eventMatch[1] as ReportStreamEvent['type'];
              const data = JSON.parse(dataMatch[1]);

              if (eventType === 'report') {
                this.currentReportId = data.id;
              }

              subject.next({ type: eventType, data });
            }
          }
        }

        subject.complete();
      })
      .catch((error) => {
        subject.next({ type: 'error', data: { message: error.message } });
        subject.complete();
      });

    return subject;
  }

  /**
   * Get a previously generated report by ID.
   */
  getReport(reportId: string): Observable<ResearchReport> {
    return this.http.get<ResearchReport>(
      `${this.apiUrl}/api/reports/${reportId}`
    );
  }

  /**
   * Ask a follow-up question about the current report.
   */
  askFollowUp(question: string): Observable<FollowUpResponse> {
    if (!this.currentReportId) {
      throw new Error('No report loaded');
    }

    return this.http.post<FollowUpResponse>(
      `${this.apiUrl}/api/reports/${this.currentReportId}/followup`,
      {
        report_id: this.currentReportId,
        question,
      }
    );
  }

  /**
   * Export the current report as a PDF.
   */
  exportPdf(): void {
    if (!this.currentReportId) {
      throw new Error('No report loaded');
    }

    window.open(
      `${this.apiUrl}/api/reports/${this.currentReportId}/export/pdf`,
      '_blank'
    );
  }

  /**
   * Get the current report ID.
   */
  getCurrentReportId(): string | null {
    return this.currentReportId;
  }

  /**
   * Reset the service state.
   */
  resetReport(): void {
    this.currentReportId = null;
  }
}
