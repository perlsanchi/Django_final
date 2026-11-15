from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.mobile}"

class OTPRecord(models.Model):
    mobile = models.CharField(max_length=15, db_index=True)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    email = models.EmailField(blank=True, null=True) 
    
    # --- ADD THESE TWO NEW COLUMNS ---
    stage = models.CharField(max_length=20, default='PREOTP')
    status = models.CharField(max_length=1, default='Z')
    # ---------------------------------

    class Meta:
        ordering = ['created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.mobile} - {self.otp_code} - {self.status} - {self.stage}"

class NSEBarred(models.Model):
    nmobile = models.CharField(max_length=15, db_index=True)
    barred = models.CharField(max_length=2)

    class Meta:
        pass
    def __str__(self):
        return f"{self.nmobile} - {self.barred}"