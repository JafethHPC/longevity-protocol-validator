import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Paper, PaperService } from './services/paper.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  paperService = inject(PaperService);

  searchQuery = '';
  papers: Paper[] = [];
  isLoading = false;

  onSearch() {
    if (!this.searchQuery.trim()) return;

    this.isLoading = true;
    this.papers = [];

    this.paperService.search(this.searchQuery).subscribe({
      next: (results: Paper[]) => {
        this.papers = results;
        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Search failed:', err);
        this.isLoading = false;
        alert('Backend error. Check console.');
      },
    });
  }
}
