import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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
  context_used: string;
}

@Injectable({
  providedIn: 'root',
})
export class PaperService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000';

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
}
