import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Source, ResearchReport } from '../../../../core/models';

@Component({
  selector: 'app-sources-tab',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="animate-fade-in">
      <h3 class="text-lg font-semibold text-stone-800 mb-4">
        Sources ({{ report.sources.length }})
      </h3>

      <div class="space-y-3">
        <div
          *ngFor="let source of report.sources"
          class="bg-white rounded-lg border border-stone-200 overflow-hidden transition-shadow hover:shadow-md"
        >
          <!-- Source Header -->
          <button
            (click)="toggleSource(source.index)"
            class="w-full px-4 py-3 flex items-start gap-3 text-left hover:bg-stone-50 transition-colors"
          >
            <span
              class="flex-shrink-0 w-6 h-6 rounded bg-emerald-100 text-emerald-700 flex items-center justify-center text-sm font-medium"
            >
              {{ source.index }}
            </span>
            <div class="flex-1 min-w-0">
              <h4 class="font-medium text-stone-800 leading-tight">
                {{ source.title }}
              </h4>
              <p class="text-sm text-stone-500 mt-1">
                {{ source.journal }} ({{ source.year }})
                <span *ngIf="source.pmid"> • PMID: {{ source.pmid }}</span>
              </p>
            </div>
            <svg
              class="w-5 h-5 text-stone-400 transition-transform flex-shrink-0"
              [class.rotate-180]="isExpanded(source.index)"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          <!-- Expanded Content -->
          <div
            *ngIf="isExpanded(source.index)"
            class="px-4 pb-4 border-t border-stone-100 animate-fade-in"
          >
            <div class="mt-3 pt-3">
              <h5 class="text-sm font-medium text-stone-600 mb-2">Abstract</h5>
              <p class="text-sm text-stone-600 leading-relaxed">
                {{ source.abstract }}
              </p>

              <div
                *ngIf="source.relevance_reason"
                class="mt-3 p-3 bg-emerald-50 rounded-lg"
              >
                <h5 class="text-sm font-medium text-emerald-700 mb-1">
                  Why This Paper?
                </h5>
                <p class="text-sm text-emerald-600">
                  {{ source.relevance_reason }}
                </p>
              </div>

              <div class="mt-4 flex items-center gap-4">
                <a
                  [href]="source.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-1 text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                >
                  <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                  View on PubMed
                </a>
                <span
                  *ngIf="source.citation_count"
                  class="text-sm text-stone-500"
                >
                  {{ source.citation_count }} citations
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      button {
        cursor: pointer;
      }
    `,
  ],
})
export class SourcesTabComponent {
  @Input({ required: true }) report!: ResearchReport;
  @Input() expandedSources: Set<number> = new Set();
  @Output() toggleSourceExpanded = new EventEmitter<number>();

  toggleSource(index: number): void {
    this.toggleSourceExpanded.emit(index);
  }

  isExpanded(index: number): boolean {
    return this.expandedSources.has(index);
  }
}
