import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SendOtpResponse {
  success: boolean;
  message: string;
  expires_at: string;
}

export interface VerifyOtpResponse {
  success: boolean;
  message: string;
}

@Injectable({ providedIn: 'root' })
export class OtpService {
  private baseUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  sendOtp(mobile: string): Observable<SendOtpResponse> {
    return this.http.post<SendOtpResponse>(`${this.baseUrl}/send-otp/`, { mobile });
  }

  verifyOtp(mobile: string, otp: string): Observable<VerifyOtpResponse> {
    return this.http.post<VerifyOtpResponse>(`${this.baseUrl}/verify-otp/`, { mobile, otp });
  }
}