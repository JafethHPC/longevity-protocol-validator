import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Paper {
  title: string;
  abstract: string;
  year: number;
  distance: number;
}

export interface SearchRequest {
  query: string;
  limit: number;
}

export interface StreamEvent {
  type: 'status' | 'token' | 'protocols' | 'complete' | 'error';
  data: any;
}

@Injectable({
  providedIn: 'root',
})
export class PaperService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;
  private currentThreadId: string | null = null;

  search(query: string): Observable<Paper[]> {
    return this.http.post<Paper[]>(`${this.apiUrl}/search`, {
      query: query,
      limit: 3,
    });
  }

  researchStream(topic: string): Subject<StreamEvent> {
    const subject = new Subject<StreamEvent>();

    const threadParam = this.currentThreadId
      ? `&thread_id=${this.currentThreadId}`
      : '';
    const url = `${this.apiUrl}/chat/stream?query=${encodeURIComponent(
      topic
    )}${threadParam}`;

    const eventSource = new EventSource(url);

    eventSource.addEventListener('status', (event: MessageEvent) => {
      subject.next({ type: 'status', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('token', (event: MessageEvent) => {
      subject.next({ type: 'token', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('protocols', (event: MessageEvent) => {
      subject.next({ type: 'protocols', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('complete', (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      this.currentThreadId = data.thread_id;
      subject.next({ type: 'complete', data });
      eventSource.close();
      subject.complete();
    });

    eventSource.addEventListener('error', (event: MessageEvent) => {
      if (event.data) {
        subject.next({ type: 'error', data: JSON.parse(event.data) });
      }
      eventSource.close();
      subject.complete();
    });

    eventSource.onerror = () => {
      subject.next({ type: 'error', data: { message: 'Connection lost' } });
      eventSource.close();
      subject.complete();
    };

    return subject;
  }

  resetThread(): void {
    this.currentThreadId = null;
  }
}
