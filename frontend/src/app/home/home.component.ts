import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../services/api.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../header/header.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HeaderComponent
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent implements OnInit {
  githubUrl = '';
  isLoading = false;
  error = '';
  repositories: any[] = [];
  showSearch = false;
  searchQuery = '';

  constructor(private apiService: ApiService, private router: Router) {}

  ngOnInit() {
    this.loadRepositories();
  }

  loadRepositories() {
    this.apiService.getRepositories().subscribe({
      next: (repos) => this.repositories = repos,
      error: () => {}
    });
  }

  indexRepo() {
    if (!this.githubUrl.trim()) return;

    this.isLoading = true;
    this.error = '';

    this.apiService.indexRepository(this.githubUrl).subscribe({
      next: () => {
        this.isLoading = false;
        this.githubUrl = '';
        this.loadRepositories();
      },
      error: () => {
        this.isLoading = false;
        this.error = 'Failed to index repository. Please check the URL and try again.';
      }
    });
  }

  openChat(repo: any) {
    this.router.navigate(['/chat', repo.id, repo.name]);
  }

  deleteRepo(repo: any) {
    this.apiService.deleteRepository(repo.id).subscribe({
      next: () => {
        this.loadRepositories();
      },
      error: () => {
        this.error = 'Failed to delete repository.';
      }
    });
  }



toggleSearch() {
  this.showSearch = !this.showSearch;
  if (!this.showSearch) this.searchQuery = '';
}

get filteredRepos() {
  if (!this.searchQuery.trim()) return this.repositories;
  return this.repositories.filter(repo =>
    repo.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
    repo.github_url.toLowerCase().includes(this.searchQuery.toLowerCase())
  );
}

}