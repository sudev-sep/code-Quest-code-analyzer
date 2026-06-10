import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { ChatComponent } from './chat/chat.component';
import { LoginComponent } from './login/login.component';
import { HeaderComponent } from './header/header.component';
import { RegisterComponent } from './register/register.component';

export const routes: Routes = [
    { path: 'Home', component: HomeComponent },
    { path: '', component: LoginComponent },
    { path: 'login', component: LoginComponent },
    { path: 'chat/:repoId/:repoName', component: ChatComponent },
    { path: 'header', component: HeaderComponent },
    { path: 'register', component: RegisterComponent },


    

];
