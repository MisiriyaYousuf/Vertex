from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='profile')
    phone = models.CharField(max_length=15, blank=False, null=False,unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    blocked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Profile"

class OTP(models.Model):
   
    email = models.EmailField()
    otp_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_verified", "is_used"]),
            models.Index(fields=["expires_at"])
        ]

    def __str__(self):
        status = "Verified" if self.is_verified else "Pending"
        return f"OTP for {self.email} - {status}"

