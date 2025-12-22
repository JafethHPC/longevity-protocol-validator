import { Component, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { ResearchSettingsComponent } from '../research-settings/research-settings.component';
import {
  ResearchConfig,
  DEFAULT_RESEARCH_CONFIG,
} from '../../../../core/models/report.model';

/**
 * Search request including question and optional config overrides
 */
export interface SearchRequest {
  question: string;
  config: Partial<ResearchConfig>;
}

@Component({
  selector: 'app-search-input',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TranslateModule,
    ResearchSettingsComponent,
  ],
  templateUrl: './search-input.component.html',
})
export class SearchInputComponent {
  @Output() search = new EventEmitter<SearchRequest>();

  query = '';
  currentConfig = signal<Partial<ResearchConfig>>({});

  exampleQueries = [
    {
      labelKey: 'search.examples.creatine',
      query: 'What is the optimal dosage of creatine for muscle growth?',
    },
    {
      labelKey: 'search.examples.sleep',
      query: 'What are the benefits of 7-8 hours of sleep per night?',
    },
    {
      labelKey: 'search.examples.fasting',
      query: 'What are the metabolic benefits of intermittent fasting?',
    },
  ];

  selectExample(example: { labelKey: string; query: string }): void {
    this.query = example.query;
  }

  handleKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey && this.query.trim()) {
      event.preventDefault();
      this.submit();
    }
  }

  onConfigChange(config: Partial<ResearchConfig>): void {
    this.currentConfig.set(config);
  }

  submit(): void {
    if (this.query.trim()) {
      this.search.emit({
        question: this.query.trim(),
        config: this.currentConfig(),
      });
    }
  }
}
