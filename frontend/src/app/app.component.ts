import { Component } from '@angular/core';
import { ReportPageComponent } from './features/report/report-page.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ReportPageComponent],
  template: `<app-report-page />`,
})
export class AppComponent {}
