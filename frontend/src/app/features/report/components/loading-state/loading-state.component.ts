import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="flex flex-col items-center justify-center py-20 animate-fade-in"
    >
      <div class="relative">
        <!-- Outer ring -->
        <div class="w-16 h-16 border-4 border-stone-200 rounded-full"></div>
        <!-- Spinning ring -->
        <div
          class="absolute top-0 left-0 w-16 h-16 border-4 border-emerald-600 rounded-full border-t-transparent animate-spin"
        ></div>
      </div>

      <p class="mt-6 text-lg text-stone-600">{{ message }}</p>

      <div class="mt-4 flex items-center gap-2 text-sm text-stone-500">
        <svg
          class="w-4 h-4 text-emerald-600"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clip-rule="evenodd"
          />
        </svg>
        <span>Searching PubMed & Semantic Scholar</span>
      </div>
    </div>
  `,
})
export class LoadingStateComponent {
  @Input() message = 'Generating report...';
}
