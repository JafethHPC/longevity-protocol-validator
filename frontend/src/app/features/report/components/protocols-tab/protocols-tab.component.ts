import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Protocol, ResearchReport } from '../../../../core/models';

@Component({
  selector: 'app-protocols-tab',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './protocols-tab.component.html',
})
export class ProtocolsTabComponent {
  @Input({ required: true }) report!: ResearchReport;
}
