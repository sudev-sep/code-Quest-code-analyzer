import { Component } from '@angular/core';
import { AuthService } from '../service/auth.service';
import { RouterModule  } from '@angular/router';
import { Router } from '@angular/router';
import { FormsModule, NgForm } from '@angular/forms';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-register',
  imports: [
    RouterModule,
    FormsModule,
    CommonModule
  ],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css'
})
export class RegisterComponent {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  registerData = {
    username: '',
    email: '',
    password: ''
  };
  onSubmit() {
    this.authService.register(this.registerData).subscribe({
      next: (response) => {
        alert('Registration successful! Please log in.');
        this.router.navigate(['/login']);
      },
      error: (error) => {
        console.error('Registration failed', error);
        alert('Registration failed. Please check your input and try again.');
      }
    });
  }

}
