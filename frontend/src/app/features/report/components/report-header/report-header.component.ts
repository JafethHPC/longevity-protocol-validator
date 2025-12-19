import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { ResearchReport } from '../../../../core/models';

@Component({
  selector: 'app-report-header',
  standalone: true,
  imports: [CommonModule, TranslateModule],
  templateUrl: './report-header.component.html',
})
export class ReportHeaderComponent {
  @Input({ required: true }) report!: ResearchReport;

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }
}
