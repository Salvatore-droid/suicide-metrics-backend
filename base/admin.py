from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, RegistrationRequest

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'department', 'role', 'is_approved', 'is_active')
    list_filter = ('user_type', 'department', 'is_approved', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('user_type', 'phone_number', 'staff_id', 'department', 'role', 'is_approved')
        }),
    )

@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'submitted_at')
    actions = ['approve_registrations', 'reject_registrations']
    
    def approve_registrations(self, request, queryset):
        for registration in queryset:
            registration.status = 'approved'
            registration.reviewed_at = timezone.now()
            registration.reviewed_by = request.user
            registration.user.is_approved = True
            registration.user.is_active = True
            registration.user.save()
            registration.save()
        
        self.message_user(request, f"{queryset.count()} registration(s) approved.")
    
    def reject_registrations(self, request, queryset):
        for registration in queryset:
            registration.status = 'rejected'
            registration.reviewed_at = timezone.now()
            registration.reviewed_by = request.user
            registration.user.is_active = False
            registration.user.save()
            registration.save()
        
        self.message_user(request, f"{queryset.count()} registration(s) rejected.")
    
    approve_registrations.short_description = "Approve selected registrations"
    reject_registrations.short_description = "Reject selected registrations"