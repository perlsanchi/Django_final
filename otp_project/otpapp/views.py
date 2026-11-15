from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated # <--- NEW: Import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken # <--- NEW: Import JWT Token generator
from .models import OTPRecord
from django.contrib.auth.models import User
from .models import OTPRecord, UserProfile
from .serializers import SendOTPSerializer, VerifyOTPSerializer
from .services import send_otp_call, verify_otp

from .serializers import SendOTPSerializer, VerifyOTPSerializer
from .services import send_otp_call, verify_otp


from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError  # <-- Import this
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import User
from .models import OTPRecord, UserProfile
from .serializers import SendOTPSerializer, VerifyOTPSerializer
from .services import send_otp_call, verify_otp


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mobile = serializer.validated_data['mobile']
        
        # --- ADD TRY/EXCEPT HERE ---
        try:
            record = send_otp_call(mobile)
        except ValidationError as e:
            # This catches the NSEBarred error from services.py
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        # ---------------------------

        return Response(
            {
                "success": True,
                "message": f"OTP call initiated to {mobile}",
                "expires_at": record.expires_at,
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mobile = serializer.validated_data['mobile']
        otp = serializer.validated_data['otp']

        success, message = verify_otp(mobile, otp)
        
        if success:
            # --- REAL WORLD LOGIC ---
            # 1. Find if a user with this mobile exists. If not, create a new Django User.
            profile = UserProfile.objects.filter(mobile=mobile).first()
            
            if not profile:
                # Create a new user. We use the mobile number as the username.
                user = User.objects.create_user(username=mobile)
                profile = UserProfile.objects.create(user=user, mobile=mobile)
            else:
                user = profile.user

            # 2. Generate a REAL JWT Token for this actual database user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "success": True, 
                "message": message,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh)
            }, status=status.HTTP_200_OK)

        return Response({"success": False, "message": message}, status=status.HTTP_400_BAD_REQUEST)


class SaveEmailView(APIView):
    # This now securely uses Django's built-in authentication
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # request.user is now a REAL Django User object from the database
        user = request.user 
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Save the email directly to the real Django User model
        user.email = email
        user.save()

        # Optional: Also save it to the OTPRecord for your own tracking
        record = OTPRecord.objects.filter(mobile=user.username, verified=True).order_by('-created_at').first()
        if record:
            record.email = email
            record.save()

        return Response({"success": True, "message": "Email saved successfully!"})