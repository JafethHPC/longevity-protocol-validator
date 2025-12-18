import {
  Component,
  inject,
  ViewChild,
  ElementRef,
  AfterViewChecked,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PaperService, StreamEvent } from './services/paper.service';
import { MarkdownPipe } from './pipes/markdown.pipe';

interface Message {
  role: 'user' | 'ai';
  text?: string;
  protocols?: any[];
  isStreaming?: boolean;
}

interface Evidence {
  title: string;
  abstract: string;
  filename?: string;
  url?: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownPipe],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements AfterViewChecked {
  @ViewChild('chatContainer') private chatContainer!: ElementRef;

  paperService = inject(PaperService);
  activeEvidence: Evidence[] = [];

  messages: Message[] = [];
  currentInput = '';
  isLoading = false;
  currentStatus = '';

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    try {
      if (this.chatContainer) {
        this.chatContainer.nativeElement.scrollTop =
          this.chatContainer.nativeElement.scrollHeight;
      }
    } catch (err) {
      console.error('Scroll error:', err);
    }
  }

  sendMessage() {
    if (!this.currentInput.trim()) return;

    const userText = this.currentInput;
    this.currentInput = '';
    this.isLoading = true;
    this.currentStatus = 'Connecting...';

    this.messages.push({ role: 'user', text: userText });

    let aiMessage: Message | null = null;

    const stream = this.paperService.researchStream(userText);

    stream.subscribe({
      next: (event: StreamEvent) => {
        switch (event.type) {
          case 'status':
            this.currentStatus = event.data.message;
            break;

          case 'token':
            if (!aiMessage) {
              aiMessage = {
                role: 'ai',
                text: event.data.text,
                protocols: [],
                isStreaming: true,
              };
              this.messages.push(aiMessage);
            } else {
              aiMessage.text = event.data.text;
            }
            break;

          case 'protocols':
            if (aiMessage) {
              aiMessage.protocols = event.data.protocols;
            }
            break;

          case 'complete':
            if (aiMessage) {
              aiMessage.isStreaming = false;
            }
            this.isLoading = false;
            this.currentStatus = '';
            break;

          case 'error':
            if (!aiMessage) {
              aiMessage = {
                role: 'ai',
                text: `Error: ${event.data.message}`,
                protocols: [],
                isStreaming: false,
              };
              this.messages.push(aiMessage);
            } else {
              aiMessage.text = `Error: ${event.data.message}`;
              aiMessage.isStreaming = false;
            }
            this.isLoading = false;
            this.currentStatus = '';
            break;
        }
      },
      error: (err) => {
        if (!aiMessage) {
          aiMessage = {
            role: 'ai',
            text: 'An error occurred while processing your request.',
            protocols: [],
            isStreaming: false,
          };
          this.messages.push(aiMessage);
        } else {
          aiMessage.text = 'An error occurred while processing your request.';
          aiMessage.isStreaming = false;
        }
        this.isLoading = false;
        this.currentStatus = '';
        console.error('Stream error:', err);
      },
      complete: () => {
        if (aiMessage) {
          aiMessage.isStreaming = false;
        }
        this.isLoading = false;
        this.currentStatus = '';
      },
    });
  }

  newChat() {
    this.messages = [];
    this.activeEvidence = [];
    this.paperService.resetThread();
  }
}
