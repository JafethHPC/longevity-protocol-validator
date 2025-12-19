import { Component, inject } from '@angular/core';
import { TranslateService, TranslateModule } from '@ngx-translate/core';
import { ReportPageComponent } from './features/report/report-page.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ReportPageComponent, TranslateModule],
  templateUrl: './app.component.html',
})
export class AppComponent {
  private readonly translate = inject(TranslateService);

  constructor() {
    this.translate.use('en');
  }
}
