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
  filename?: string;
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

  isResearchMode = false;
  isAgentWorking = false;

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
      const [titlePart, rest1] = chunk.split('Source: ');

      if (!rest1) {
        const [t, a] = chunk.split('Abstract: ');
        return {
          title: t.trim(),
          abstract: a ? a.trim() : '',
        };
      }

      const [sourcePart, abstractPart] = rest1.split('Abstract: ');

      return {
        title: titlePart ? titlePart.trim() : 'Unknown Source',
        abstract: abstractPart ? abstractPart.trim() : '',
        filename: sourcePart ? sourcePart.trim() : undefined,
      };
    });
  }

  toggleMode() {
    this.isResearchMode = !this.isResearchMode;
  }

  triggerAgent() {
    if (!this.currentInput.trim()) return;

    const topic = this.currentInput;
    this.currentInput = '';
    this.isAgentWorking = true;

    this.messages.push({ role: 'user', text: topic });
    this.messages.push({
      role: 'ai',
      text: 'Thinking... This may take a moment.',
    });

    this.paperService.research(topic).subscribe({
      next: (response) => {
        this.isAgentWorking = false;
        this.messages.push({ role: 'ai', text: response.result });
      },
      error: (error) => {
        this.isAgentWorking = false;
        this.messages.push({
          role: 'ai',
          text: 'An error occurred while researching.',
        });
        console.error(error);
      },
    });
  }
}
