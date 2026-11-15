import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
import logging

from .models import OTPRecord

logger = logging.getLogger(__name__)

def generate_otp(length=None):
    length = length or getattr(settings, 'OTP_LENGTH', 6)
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def send_otp_call(mobile):
    otp = generate_otp()
    expires_at = timezone.now() + timedelta(seconds=getattr(settings, 'OTP_EXPIRY_SECONDS', 300))

    # 1. Find ONE existing active PREOTP record for this mobile (the latest one)
    existing_record = OTPRecord.objects.filter(
        mobile=mobile, 
        stage='PREOTP', 
        status='Z'
    ).order_by('-created_at').first()  # <--- .first() gets only ONE record

    # 2. Mark only that ONE record as 'R' (Rejected)
    if existing_record:
        existing_record.status = 'R'
        existing_record.save(update_fields=['status'])

    # 3. Create the new record with stage 'PREOTP' and status 'Z'
    record = OTPRecord.objects.create(
        mobile=mobile,
        otp_code=otp,
        expires_at=expires_at,
        stage='PREOTP',
        status='Z'
    )

    # ==========================================
    # SIMULATED SMS (PRINTS TO TERMINAL)
    # ==========================================
    print(f"\n📱 [SIMULATED SMS to {mobile}] Your OTP is: {otp}\n")

    return record


def verify_otp(mobile, code):
    """
    Returns (success: bool, message: str)
    """
    # 1. Find the active PREOTP record
    record = OTPRecord.objects.filter(
        mobile=mobile, 
        stage='PREOTP', 
        status='Z'
    ).order_by('-created_at').first()

    if not record:
        return False, "No active OTP found for this number."

    if record.is_expired():
        return False, "OTP has expired."

    if record.attempts >= getattr(settings, 'OTP_MAX_ATTEMPTS', 5):
        return False, "Too many attempts. Request a new OTP."

    record.attempts += 1

    if record.otp_code != code:
        record.save(update_fields=['attempts'])
        return False, f"Invalid OTP. {getattr(settings, 'OTP_MAX_ATTEMPTS', 5) - record.attempts} attempts left."

    # 2. Success! Update the record to the next stage
    record.verified = True
    record.stage = 'EMAIL'  # Move to email stage
    record.status = 'A'     # 'A' for Approved/Active
    record.save(update_fields=['verified', 'attempts', 'stage', 'status'])
    
    return True, "OTP verified successfully."