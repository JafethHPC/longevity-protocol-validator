import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export type TabId = 'findings' | 'protocols' | 'sources';

export interface Tab {
  id: TabId;
  label: string;
  count?: number;
}

@Component({
  selector: 'app-tab-bar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex border-b border-stone-200">
      <button
        *ngFor="let tab of tabs"
        (click)="selectTab(tab.id)"
        [class]="getTabClasses(tab.id)"
      >
        {{ tab.label }}
        <span
          *ngIf="tab.count !== undefined"
          class="ml-2 px-2 py-0.5 text-xs rounded-full"
          [class.bg-emerald-100]="activeTab === tab.id"
          [class.text-emerald-700]="activeTab === tab.id"
          [class.bg-stone-100]="activeTab !== tab.id"
          [class.text-stone-500]="activeTab !== tab.id"
        >
          {{ tab.count }}
        </span>
      </button>
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
export class TabBarComponent {
  @Input({ required: true }) tabs: Tab[] = [];
  @Input() activeTab: TabId = 'findings';
  @Output() tabChange = new EventEmitter<TabId>();

  selectTab(tabId: TabId): void {
    this.tabChange.emit(tabId);
  }

  getTabClasses(tabId: TabId): string {
    const base = 'px-4 py-3 text-sm font-medium transition-colors relative';
    const active = 'text-emerald-600 border-b-2 border-emerald-600 -mb-px';
    const inactive = 'text-stone-500 hover:text-stone-700 hover:bg-stone-50';

    return `${base} ${tabId === this.activeTab ? active : inactive}`;
  }
}
