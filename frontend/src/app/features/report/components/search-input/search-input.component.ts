import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-search-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search-input.component.html',
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
