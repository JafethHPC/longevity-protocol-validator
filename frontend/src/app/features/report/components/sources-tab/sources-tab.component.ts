import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { Source, ResearchReport } from '../../../../core/models';

@Component({
  selector: 'app-sources-tab',
  standalone: true,
  imports: [CommonModule, TranslateModule],
  templateUrl: './sources-tab.component.html',
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
