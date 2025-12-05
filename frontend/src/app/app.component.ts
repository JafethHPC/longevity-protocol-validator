import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatResponse, PaperService } from './services/paper.service';
import { MarkdownPipe } from './pipes/markdown.pipe';

interface Message {
  role: 'user' | 'ai';
  text?: string;
  data?: ChatResponse;
}

interface Evidence {
  title: string;
  abstract: string;
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
  activeEvidence: Evidence[] = [];

  messages: Message[] = [];
  currentInput = '';
  isLoading = false;

  sendMessage() {
    if (!this.currentInput.trim()) return;

    const userText = this.currentInput;
    this.currentInput = '';
    this.isLoading = true;

    this.messages.push({ role: 'user', text: userText });

    this.paperService.chat(userText).subscribe({
      next: (response: any) => {
        this.isLoading = false;
        this.messages.push({ role: 'ai', data: response });

        this.activeEvidence = this.parseEvidence(response.context_used);
      },
      error: (error: any) => {
        this.isLoading = false;
        this.messages.push({
          role: 'ai',
          text: 'An error occurred while processing your request.',
        });
        console.error('Error:', error);
      },
    });
  }

  parseEvidence(contextString: string): Evidence[] {
    if (!contextString) return [];

    const rawChunks = contextString
      .split('Paper: ')
      .filter((chunk) => chunk.trim().length > 0);

    return rawChunks.map((chunk) => {
      const [titlePart, ...abstractParts] = chunk.split('Abstract: ');
      return {
        title: titlePart ? titlePart.trim() : 'Unknown Source',
        abstract: abstractParts.join('Abstract: ').trim(),
      };
    });
  }
}
