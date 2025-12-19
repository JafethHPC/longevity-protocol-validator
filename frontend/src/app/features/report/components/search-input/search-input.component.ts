import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-search-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="max-w-3xl mx-auto mt-20 animate-fade-in">
      <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-stone-800 mb-3">
          What would you like to research?
        </h2>
        <p class="text-stone-600">
          Enter a scientific question and we'll analyze the latest research
          papers.
        </p>
      </div>

      <div class="bg-white rounded-2xl shadow-lg p-6 border border-stone-200">
        <textarea
          [(ngModel)]="query"
          (keydown)="handleKeydown($event)"
          placeholder="e.g., What are the cognitive benefits of intermittent fasting?"
          rows="3"
          class="w-full px-4 py-3 text-lg border border-stone-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 resize-none transition-all"
        ></textarea>

        <div class="flex items-center justify-between mt-4">
          <div class="flex flex-wrap gap-2">
            <button
              *ngFor="let example of exampleQueries"
              (click)="selectExample(example)"
              class="text-sm px-3 py-1.5 rounded-full bg-stone-100 text-stone-600 hover:bg-stone-200 transition-colors"
            >
              {{ example.label }}
            </button>
          </div>

          <button
            (click)="submit()"
            [disabled]="!query.trim()"
            class="px-6 py-2.5 bg-emerald-600 text-white font-medium rounded-xl hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            Generate Report
          </button>
        </div>
      </div>
    </div>
  `,
})
export class SearchInputComponent {
  @Output() search = new EventEmitter<string>();

  query = '';

  exampleQueries = [
    {
      label: 'Creatine dosage',
      query: 'What is the optimal dosage of creatine for muscle growth?',
    },
    {
      label: 'Sleep duration',
      query: 'What are the benefits of 7-8 hours of sleep per night?',
    },
    {
      label: 'Intermittent fasting',
      query: 'What are the metabolic benefits of intermittent fasting?',
    },
  ];

  selectExample(example: { label: string; query: string }): void {
    this.query = example.query;
  }

  handleKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey && this.query.trim()) {
      event.preventDefault();
      this.submit();
    }
  }

  submit(): void {
    if (this.query.trim()) {
      this.search.emit(this.query.trim());
    }
  }
}
