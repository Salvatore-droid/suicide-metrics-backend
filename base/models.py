from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('university_staff', 'University Staff'),
        ('mental_health_professional', 'Mental Health Professional'),
        ('administrator', 'Administrator'),
        ('student_counselor', 'Student Counselor'),
        ('faculty_member', 'Faculty Member'),
    )
    
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    staff_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"

class RegistrationRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='reviewed_registrations')
    rejection_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Registration request for {self.user.username} - {self.status}"

class UserSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def is_valid(self):
        return self.is_active and timezone.now() < self.expires_at