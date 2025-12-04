import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PaperService } from './services/paper.service';
import { MarkdownPipe } from './pipes/markdown.pipe';

interface Message {
  role: 'user' | 'ai';
  text: string;
  context?: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownPipe],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  paperService = inject(PaperService);

  messages: Message[] = [];
  currentInput = '';
  isLoading = false;

  sendMessage() {
    if (!this.currentInput.trim()) return;

    const userText = this.currentInput;
    this.currentInput = '';
    this.isLoading = true;

    this.messages.push({ role: 'user', text: userText});
    
    this.paperService.chat(userText).subscribe({
      next: (response: any) => {
        this.isLoading = false;
        this.messages.push({ role: 'ai', text: response.answer, context: response.context_used});
      },
      error: (error: any) => {
        this.isLoading = false;
        this.messages.push({ role: 'ai', text: 'An error occurred while processing your request.'});
        console.error('Error:', error);
      }
    })
  }
}
