import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';

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
  confidence: string;
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

export interface ReportStreamEvent {
  type: 'status' | 'report' | 'complete' | 'error';
  data: any;
}

@Injectable({
  providedIn: 'root',
})
export class ReportService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;
  private currentReportId: string | null = null;

  generateReport(
    question: string,
    maxSources: number = 10
  ): Subject<ReportStreamEvent> {
    const subject = new Subject<ReportStreamEvent>();

    const url = `${this.apiUrl}/api/reports/generate/stream`;

    // Use fetch with POST for SSE
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

          // Process complete events from buffer
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

  getReport(reportId: string): Observable<ResearchReport> {
    return this.http.get<ResearchReport>(
      `${this.apiUrl}/api/reports/${reportId}`
    );
  }

  askFollowUp(
    question: string
  ): Observable<{ question: string; answer: string; report_id: string }> {
    if (!this.currentReportId) {
      throw new Error('No report loaded');
    }

    return this.http.post<{
      question: string;
      answer: string;
      report_id: string;
    }>(`${this.apiUrl}/api/reports/${this.currentReportId}/followup`, {
      report_id: this.currentReportId,
      question,
    });
  }

  getCurrentReportId(): string | null {
    return this.currentReportId;
  }

  resetReport(): void {
    this.currentReportId = null;
  }

  exportPdf(): void {
    if (!this.currentReportId) {
      throw new Error('No report loaded');
    }

    // Open PDF in new tab (browser will download it)
    window.open(
      `${this.apiUrl}/api/reports/${this.currentReportId}/export/pdf`,
      '_blank'
    );
  }
}
