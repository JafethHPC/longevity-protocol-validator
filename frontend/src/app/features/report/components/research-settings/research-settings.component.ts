import { Component, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ResearchConfig,
  DEFAULT_RESEARCH_CONFIG,
} from '../../../../core/models/report.model';

@Component({
  selector: 'app-research-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './research-settings.component.html',
})
export class ResearchSettingsComponent {
  @Output() configChange = new EventEmitter<Partial<ResearchConfig>>();

  // Track which sections are expanded
  isExpanded = signal(false);
  showAdvanced = signal(false);

  // Form values (using defaults)
  config = signal<ResearchConfig>({ ...DEFAULT_RESEARCH_CONFIG });

  toggleExpanded(): void {
    this.isExpanded.update((v) => !v);
  }

  toggleAdvanced(): void {
    this.showAdvanced.update((v) => !v);
  }

  updateConfig(key: keyof ResearchConfig, value: any): void {
    this.config.update((c) => ({ ...c, [key]: value }));
    this.emitConfig();
  }

  resetToDefaults(): void {
    this.config.set({ ...DEFAULT_RESEARCH_CONFIG });
    this.emitConfig();
  }

  private emitConfig(): void {
    this.configChange.emit(this.config());
  }

  // Helper to get current config value
  get(key: keyof ResearchConfig): any {
    return this.config()[key];
  }
}
