
import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root',
})
export class AuthService {

  private API_URL = 'http://127.0.0.1:8000/api';
  private isBrowser: boolean;

  constructor(
    private http: HttpClient,
    private router: Router,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  register(data: any): Observable<any> {
    return this.http.post(
      `${this.API_URL}/auth/register/`,
      data
    );
  }

  login(data: any): Observable<any> {
    return this.http.post(`${this.API_URL}/auth/login/`,data);
  } 

  

  saveToken(token: string): void {
    if (!this.isBrowser) return;
    localStorage.setItem('token', token);
  }

  getToken(): string | null {
    if (!this.isBrowser) return null;
    return localStorage.getItem('token');
  }

 

   logout() {
    localStorage.removeItem('token');
    this.router.navigate(['/login']);
  }
}
