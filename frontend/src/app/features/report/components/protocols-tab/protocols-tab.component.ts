import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { Protocol, ResearchReport } from '../../../../core/models';

@Component({
  selector: 'app-protocols-tab',
  standalone: true,
  imports: [CommonModule, TranslateModule],
  templateUrl: './protocols-tab.component.html',
})
export class ProtocolsTabComponent {
  @Input({ required: true }) report!: ResearchReport;
}
