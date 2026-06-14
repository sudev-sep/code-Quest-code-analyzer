import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private baseUrl = 'https://code-quest-code-analyzer-production.up.railway.app/api';

  constructor(private http: HttpClient) {}

  indexRepository(githubUrl: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/repositories/`, {
      github_url: githubUrl
    });
  }

  getRepositories(): Observable<any> {
    return this.http.get(`${this.baseUrl}/repositories/`);
  }

  askQuestion(repoId: number, question: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/repositories/${repoId}/ask/`, {
      question: question
    });
  }

  deleteRepository(repoId: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/repositories/${repoId}/delete/`);
  }
}