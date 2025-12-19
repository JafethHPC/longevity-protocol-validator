import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { ResearchProgress, ProgressStep } from '../../../../core/models';

@Component({
  selector: 'app-research-progress',
  standalone: true,
  imports: [CommonModule, TranslateModule],
  templateUrl: './loading-state.component.html',
  styleUrl: './loading-state.component.scss',
})
export class ResearchProgressComponent {
  @Input({ required: true }) progress!: ResearchProgress;

  getStepTextClass(status: string): string {
    switch (status) {
      case 'complete':
        return 'text-emerald-700';
      case 'active':
        return 'text-stone-800';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-stone-400';
    }
  }
}
