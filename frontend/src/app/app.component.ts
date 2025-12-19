import { Component } from '@angular/core';
import { ReportPageComponent } from './features/report/report-page.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ReportPageComponent],
  templateUrl: './app.component.html',
})
export class AppComponent {}
