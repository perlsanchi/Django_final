import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
import logging

# Twilio imports commented out
# from twilio.rest import Client
# from twilio.base.exceptions import TwilioRestException

from .models import OTPRecord

logger = logging.getLogger(__name__)


def generate_otp(length=None):
    length = length or getattr(settings, 'OTP_LENGTH', 6)
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def send_otp_call(mobile):
    otp = generate_otp()
    expires_at = timezone.now() + timedelta(seconds=settings.OTP_EXPIRY_SECONDS)

    # Invalidate any prior unverified OTPs for this number
    OTPRecord.objects.filter(mobile=mobile, verified=False).update(verified=True)

    record = OTPRecord.objects.create(
        mobile=mobile,
        otp_code=otp,
        expires_at=expires_at,
    )

    # ==========================================
    # TWILIO SMS SENDING (COMMENTED OUT)
    # ==========================================
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    #
    # try:
    #     message = client.messages.create(
    #         body=f"Your OTP is {otp}. It expires in 5 minutes.",
    #         from_=settings.TWILIO_FROM_NUMBER,
    #         to=mobile,
    #     )
    #     logger.info(f"SMS sent to {mobile}, SID: {message.sid}")
    # except TwilioRestException as e:
    #     logger.error(f"Twilio SMS failed: {e.code} - {e.msg}")
    #     raise
    # except Exception as e:
    #     logger.error(f"Unexpected error sending SMS: {e}")
    #     raise

    # ==========================================
    # SIMULATED SMS (PRINTS TO TERMINAL)
    # ==========================================
    print(f"\n📱 [SIMULATED SMS to {mobile}] Your OTP is: {otp}\n")

    return record


def verify_otp(mobile, code):
    """
    Returns (success: bool, message: str)
    """
    record = OTPRecord.objects.filter(
        mobile=mobile, verified=False
    ).order_by('-created_at').first()

    if not record:
        return False, "No active OTP found for this number."

    if record.is_expired():
        return False, "OTP has expired."

    if record.attempts >= settings.OTP_MAX_ATTEMPTS:
        return False, "Too many attempts. Request a new OTP."

    record.attempts += 1

    if record.otp_code != code:
        record.save(update_fields=['attempts'])
        return False, f"Invalid OTP. {settings.OTP_MAX_ATTEMPTS - record.attempts} attempts left."

    record.verified = True
    record.save(update_fields=['verified', 'attempts'])
    return True, "OTP verified successfully."