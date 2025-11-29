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
}
