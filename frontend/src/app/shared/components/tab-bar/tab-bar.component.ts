import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';

export type TabId = 'findings' | 'protocols' | 'sources';

export interface Tab {
  id: TabId;
  labelKey: string;
  count?: number;
}

@Component({
  selector: 'app-tab-bar',
  standalone: true,
  imports: [CommonModule, TranslateModule],
  templateUrl: './tab-bar.component.html',
})
export class TabBarComponent {
  @Input({ required: true }) tabs: Tab[] = [];
  @Input() activeTab: TabId = 'findings';
  @Output() tabChange = new EventEmitter<TabId>();

  selectTab(tabId: TabId): void {
    this.tabChange.emit(tabId);
  }

  getTabClasses(tabId: TabId): string {
    const base =
      'px-4 py-3 text-sm font-medium transition-colors relative cursor-pointer';
    const active = 'text-emerald-600 border-b-2 border-emerald-600 -mb-px';
    const inactive = 'text-stone-500 hover:text-stone-700 hover:bg-stone-50';

    return `${base} ${tabId === this.activeTab ? active : inactive}`;
  }
}
