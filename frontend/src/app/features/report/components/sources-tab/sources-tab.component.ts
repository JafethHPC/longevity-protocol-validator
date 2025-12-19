import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Source, ResearchReport } from '../../../../core/models';

@Component({
  selector: 'app-sources-tab',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sources-tab.component.html',
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
