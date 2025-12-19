import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { Finding, ResearchReport } from '../../../../core/models';
import { MarkdownPipe } from '../../../../shared/pipes/markdown.pipe';

@Component({
  selector: 'app-findings-tab',
  standalone: true,
  imports: [CommonModule, TranslateModule, MarkdownPipe],
  templateUrl: './findings-tab.component.html',
})
export class FindingsTabComponent {
  @Input({ required: true }) report!: ResearchReport;

  getConfidenceBadge(confidence: string): string {
    const base = 'px-2 py-0.5 rounded-full text-xs font-medium';
    const colors: Record<string, string> = {
      high: 'bg-emerald-100 text-emerald-800',
      medium: 'bg-amber-100 text-amber-800',
      low: 'bg-red-100 text-red-800',
    };
    return `${base} ${
      colors[confidence.toLowerCase()] || 'bg-stone-100 text-stone-800'
    }`;
  }

  formatSourceIndices(indices: number[]): string {
    return indices.map((i) => `[${i}]`).join(' ');
  }
}
