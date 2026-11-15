from rest_framework import serializers

class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.RegexField(
        regex=r"^\d{10}$",
        error_messages={
            "invalid": "Mobile number must be exactly 10 digits.",
            "required": "Mobile number is required.",
            "blank": "Mobile number cannot be empty."
        }
    )

class VerifyOTPSerializer(serializers.Serializer):
    mobile = serializers.RegexField(
        regex=r"^\d{10}$",
        error_messages={
            "invalid": "Mobile number must be exactly 10 digits.",
            "required": "Mobile number is required."
        }
    )
    otp = serializers.CharField(
        max_length=6, 
        min_length=6,
        error_messages={
            "min_length": "OTP must be exactly 6 digits.",
            "max_length": "OTP must be exactly 6 digits.",
            "required": "OTP is required."
        }
    )

class SaveEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "invalid": "Please enter a valid email address.",
            "required": "Email address is required."
        }
    )

"""
This code defines two DRF (Django REST Framework) serializers used to validate incoming request data for an OTP (One-Time Password) authentication flow. They are not model serializers — they only validate input, they don't touch the database.
Validates that the submitted mobile field matches the 

Optional leading + (international format)

First digit must be 1–9 (no leading zero)

Followed by 9 to 14 digits → total 10–15 digits long

If it fails, returns the custom error message "Enter a valid mobile number (10-15 digits, optional +)." instead of the default.

Purpose: ensures only properly formatted phone numbers reach your OTP-sending logic (e.g., SMS gateway).
"""