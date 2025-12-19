import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button
      [type]="type"
      [disabled]="disabled || loading"
      [class]="buttonClasses"
      (click)="handleClick($event)"
    >
      <span *ngIf="loading" class="loading-spinner">
        <svg
          class="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      </span>
      <ng-content></ng-content>
    </button>
  `,
  styles: [
    `
      button {
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        font-weight: 500;
        border-radius: 0.5rem;
        transition: all 0.2s ease;
        border: none;
        outline: none;
      }

      button:disabled {
        cursor: not-allowed;
        opacity: 0.6;
      }

      button:focus-visible {
        outline: 2px solid #059669;
        outline-offset: 2px;
      }

      .loading-spinner {
        display: inline-flex;
      }

      .animate-spin {
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        from {
          transform: rotate(0deg);
        }
        to {
          transform: rotate(360deg);
        }
      }
    `,
  ],
})
export class ButtonComponent {
  @Input() variant: ButtonVariant = 'primary';
  @Input() size: ButtonSize = 'md';
  @Input() type: 'button' | 'submit' = 'button';
  @Input() disabled = false;
  @Input() loading = false;
  @Input() fullWidth = false;

  @Output() buttonClick = new EventEmitter<MouseEvent>();

  get buttonClasses(): string {
    const base = this.fullWidth ? 'w-full' : '';
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base',
    };
    const variantClasses = {
      primary:
        'bg-emerald-600 text-white hover:bg-emerald-700 active:bg-emerald-800',
      secondary:
        'bg-stone-200 text-stone-700 hover:bg-stone-300 active:bg-stone-400',
      ghost:
        'bg-transparent text-stone-600 hover:bg-stone-100 hover:text-stone-700',
      danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800',
    };

    return `${base} ${sizeClasses[this.size]} ${
      variantClasses[this.variant]
    }`.trim();
  }

  handleClick(event: MouseEvent): void {
    if (!this.disabled && !this.loading) {
      this.buttonClick.emit(event);
    }
  }
}
