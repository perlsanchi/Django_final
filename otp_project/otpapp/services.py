import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
import logging

from .models import OTPRecord,NSEBarred

logger = logging.getLogger(__name__)

import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError  # <-- Import this
import logging

from .models import OTPRecord, NSEBarred

logger = logging.getLogger(__name__)

def generate_otp(length=None):
    length = length or getattr(settings, 'OTP_LENGTH', 6)
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def send_otp_call(mobile):
    # 1. Check if NSE Barred FIRST
    if NSEBarred.objects.filter(nmobile=mobile, barred='A').exists():
        # Raising ValidationError makes DRF return a 400 automatically
        raise ValidationError({"mobile": ["Account is NSE barred."]})

    otp = generate_otp()
    expires_at = timezone.now() + timedelta(seconds=getattr(settings, 'OTP_EXPIRY_SECONDS', 300))

    # 2. Find ONE existing active PREOTP record
    existing_record = OTPRecord.objects.filter(
        mobile=mobile, 
        stage='PREOTP', 
        status='Z'
    ).order_by('-created_at').first()

    # 3. Mark old one as 'R'
    if existing_record:
        existing_record.status = 'R'
        existing_record.save(update_fields=['status'])

    # 4. Create the new record
    record = OTPRecord.objects.create(
        mobile=mobile,
        otp_code=otp,
        expires_at=expires_at,
        stage='PREOTP',
        status='Z'
    )

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