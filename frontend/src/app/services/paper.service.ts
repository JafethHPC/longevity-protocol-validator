import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
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

export interface ChatResponse {
  answer: string;
  consensus: string[];
  conflict: string[];
  limitations: string;
  context_used: string;
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

  chat(query: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, {
      query: query,
    });
  }

  research(topic: string): Observable<{ result: string; thread_id: string }> {
    const payload = {
      query: topic,
      thread_id: this.currentThreadId,
    };

    return this.http
      .post<{ result: string; thread_id: string }>(
        `${this.apiUrl}/agent/research`,
        payload
      )
      .pipe(
        tap((response: { result: string; thread_id: string }) => {
          this.currentThreadId = response.thread_id;
        })
      );
  }
}
