import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../services/api.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { marked } from 'marked'; 
import { HeaderComponent } from '../header/header.component';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  htmlContent?: string; 
  sources?: string[];
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, HeaderComponent],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css'
})
export class ChatComponent implements OnInit {
  repoId!: number;
  repoName!: string;
  question = '';
  isLoading = false;
  messages: Message[] = [];

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) {}

  async ngOnInit() { 
    this.repoId = Number(this.route.snapshot.paramMap.get('repoId'));
    this.repoName = this.route.snapshot.paramMap.get('repoName') || 'Repository';

    // Welcome message
    const welcomeText = `Hi! I've indexed **${this.repoName}**. Ask me anything about this codebase — like "where is the login logic?" or "how does the payment flow work?"`;
    
    this.messages.push({
      role: 'assistant',
      text: welcomeText,
      htmlContent: await marked.parse(welcomeText) // <-- 4. Parse the welcome message
    });
  }

  async askQuestion() { // <-- 5. Make askQuestion async
    if (!this.question.trim() || this.isLoading) return;

    const userQuestion = this.question.trim();
    this.question = '';

    // Add user message to chat
    this.messages.push({
      role: 'user',
      text: userQuestion,
      htmlContent: await marked.parse(userQuestion) // <-- 6. Parse user message
    });

    this.isLoading = true;

    this.apiService.askQuestion(this.repoId, userQuestion).subscribe({
      next: async (response) => { // <-- 7. Make the next callback async
        this.isLoading = false;
        
        this.messages.push({
          role: 'assistant',
          text: response.answer,
          htmlContent: await marked.parse(response.answer), // <-- 8. Parse AI response
          sources: response.sources
        });

        // Scroll to bottom after response
        setTimeout(() => this.scrollToBottom(), 100);
      },
      error: async () => { // <-- 9. Make the error callback async
        this.isLoading = false;
        const errorText = 'Sorry, something went wrong. Please try again.';
        
        this.messages.push({
          role: 'assistant',
          text: errorText,
          htmlContent: await marked.parse(errorText) // <-- 10. Parse error message
        });
      }
    });

    // Scroll to bottom after user message
    setTimeout(() => this.scrollToBottom(), 100);
  }

  scrollToBottom() {
    const chatBox = document.querySelector('.messages');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
  }

  goHome() {
    this.router.navigate(['/Home']);
  }
}