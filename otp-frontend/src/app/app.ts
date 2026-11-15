import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="hero">
      <div class="overlay"></div>
      
      <div class="content-wrapper">
        <!-- Brand Header -->
        <div class="brand">
          <h1>🐟 Natasha <span>the Flavour House</span></h1>
          <p>Fresh Catch. Exquisite Flavours. Delivered to You.</p>
        </div>

        <!-- Login Card -->
        <div class="login-box">
          <h2>Secure Registration</h2>

          <!-- STEP 1: Mobile -->
          <div *ngIf="step === 'mobile'" class="step">
            <label>Mobile Number</label>
            <input type="tel" [(ngModel)]="mobile" placeholder="Enter 10-digit number" />
            <button (click)="sendOtp()" [disabled]="loading">
              {{ loading ? 'Sending OTP...' : 'Send OTP' }}
            </button>
          </div>

          <!-- STEP 2: OTP -->
          <div *ngIf="step === 'otp'" class="step">
            <p class="hint">📱 Check your phone/SMS for the OTP</p>
            <label>Enter OTP</label>
            <input type="text" [(ngModel)]="otp" maxlength="6" placeholder="6-digit code" />
            <button (click)="verifyOtp()" [disabled]="loading">
              {{ loading ? 'Verifying...' : 'Verify OTP' }}
            </button>
            <button class="link" (click)="reset()">Change Number</button>
          </div>

          <!-- STEP 3: Email -->
          <div *ngIf="step === 'email'" class="step">
            <p class="success">✅ Number Verified!</p>
            <label>Email Address</label>
            <input type="email" [(ngModel)]="email" placeholder="you@example.com" />
            <button (click)="saveEmail()" [disabled]="loading">
              {{ loading ? 'Saving...' : 'Complete Registration' }}
            </button>
          </div>

          <!-- STEP 4: Done -->
          <div *ngIf="step === 'done'" class="step">
            <p class="success">🎉 Welcome to the House!</p>
            <p>We've saved <b>{{ email }}</b> to your account.</p>
            <button (click)="reset()">Sign Out</button>
          </div>

          <!-- Error Message Display -->
          <p *ngIf="error" class="error">{{ error }}</p>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./app.css']
})
export class App {
  mobile = '';
  otp = '';
  email = '';
  step: 'mobile' | 'otp' | 'email' | 'done' = 'mobile';
  loading = false;
  error = '';

  private baseUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) {}

  sendOtp() {
    this.error = '';
    if (!this.mobile) { 
      this.error = 'Please enter a mobile number'; 
      return; 
    }
    
    this.loading = true;
    this.http.post<any>(`${this.baseUrl}/send-otp/`, { mobile: this.mobile }).subscribe({
      next: () => { 
        this.loading = false; 
        this.step = 'otp'; 
        this.cdr.detectChanges(); 
      },
      error: (err) => { 
        this.loading = false; 
        // Catch the error message sent from Django
        if (err.error && err.error.mobile) {
          this.error = err.error.mobile[0]; // e.g., "Mobile number must be exactly 10 digits."
        } else if (err.error && err.error.detail) {
          this.error = err.error.detail;
        } else {
          this.error = 'Failed to connect to server or invalid input.';
        }
        this.cdr.detectChanges(); 
      }
    });
  }

  verifyOtp() {
    this.error = '';
    if (this.otp.length !== 6) { 
      this.error = 'OTP must be 6 digits'; 
      return; 
    }
    
    this.loading = true;
    this.http.post<any>(`${this.baseUrl}/verify-otp/`, { mobile: this.mobile, otp: this.otp }).subscribe({
      next: (res) => { 
        this.loading = false; 
        if (res.access_token) {
          localStorage.setItem('access_token', res.access_token);
          this.step = 'email'; 
        }
        this.cdr.detectChanges(); 
      },
      error: (err) => { 
        this.loading = false; 
        // Catch the OTP error message sent from Django
        if (err.error && err.error.otp) {
          this.error = err.error.otp[0]; // e.g., "OTP must be exactly 6 digits."
        } else if (err.error && err.error.mobile) {
          this.error = err.error.mobile[0];
        } else if (err.error && err.error.detail) {
          this.error = err.error.detail;
        } else {
          this.error = 'Invalid OTP.';
        }
        this.cdr.detectChanges(); 
      }
    });
  }

  saveEmail() {
    this.error = '';
    if (!this.email || !this.email.includes('@')) { 
      this.error = 'Enter a valid email address'; 
      return; 
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) { 
      this.error = 'Session expired. Please restart.'; 
      this.reset(); 
      return; 
    }
    
    this.loading = true;
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    
    this.http.post<any>(`${this.baseUrl}/save-email/`, { email: this.email }, { headers }).subscribe({
      next: () => { 
        this.loading = false; 
        this.step = 'done'; 
        this.cdr.detectChanges(); 
      },
      error: (err) => { 
        this.loading = false; 
        if (err.status === 401) {
          this.error = 'Session expired.';
          this.reset();
        } else if (err.error && err.error.email) {
          this.error = err.error.email[0]; // Catch email validation error from Django
        } else {
          this.error = 'Failed to save email.'; 
        }
        this.cdr.detectChanges(); 
      }
    });
  }

  reset() {
    this.mobile = ''; 
    this.otp = ''; 
    this.email = ''; 
    this.step = 'mobile'; 
    this.error = '';
    localStorage.removeItem('access_token');
    this.cdr.detectChanges();
  }
}