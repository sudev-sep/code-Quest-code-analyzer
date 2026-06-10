import { Component } from '@angular/core';
import { AuthService } from '../service/auth.service';  
import { RouterModule  } from '@angular/router';
import { Router } from '@angular/router';
import { FormsModule, NgForm } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  imports: [FormsModule,CommonModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {

   constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  loginData = {
    username: '',
    password: ''

    
  };

 onSubmit() {
    this.authService.login(this.loginData).subscribe({
      next: (response) => {
        this.authService.saveToken(response.access);
        this.router.navigate(['/Home']);
      },
      error: (error) => {
        console.error('Login failed', error); 
        alert('Login failed. Please check your credentials and try again.');
      } 
    });
  }

}
