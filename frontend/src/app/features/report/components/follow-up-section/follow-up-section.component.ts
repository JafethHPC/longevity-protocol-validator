import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { FollowUpMessage } from '../../../../core/models';
import { MarkdownPipe } from '../../../../shared/pipes/markdown.pipe';

@Component({
  selector: 'app-follow-up-section',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule, MarkdownPipe],
  templateUrl: './follow-up-section.component.html',
})
export class FollowUpSectionComponent {
  @Input() messages: FollowUpMessage[] = [];
  @Input() isLoading = false;
  @Output() askQuestion = new EventEmitter<string>();

  newQuestion = '';

  submit(): void {
    if (this.newQuestion.trim() && !this.isLoading) {
      this.askQuestion.emit(this.newQuestion.trim());
      this.newQuestion = '';
    }
  }
}
