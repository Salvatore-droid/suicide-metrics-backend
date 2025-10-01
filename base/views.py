from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
import secrets
from .serializers import LoginSerializer
from django.core.mail import send_mail
from django.conf import settings
from .models import *
from .serializers import RegistrationSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Create session token
        token = secrets.token_urlsafe(64)
        expires_at = timezone.now() + timedelta(days=7)
        
        # Deactivate previous sessions
        UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # Create new session
        session = UserSession.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        # Prepare response data
        user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'user_type': user.user_type,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        response_data = {
            'message': 'Login successful',
            'user': user_data,
            'token': token,
            'expires_at': expires_at.isoformat(),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if token:
        try:
            session = UserSession.objects.get(token=token, is_active=True)
            session.is_active = False
            session.save()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except UserSession.DoesNotExist:
            pass
    
    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    email = request.data.get('email')
    
    try:
        user = CustomUser.objects.get(email=email)
        # Here you would typically:
        # 1. Generate password reset token
        # 2. Send email with reset link
        # 3. Return success message
        
        return Response({
            'message': 'Password reset instructions have been sent to your email'
        }, status=status.HTTP_200_OK)
        
    except CustomUser.DoesNotExist:
        # For security, don't reveal if email exists
        return Response({
            'message': 'If your email exists in our system, you will receive reset instructions'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Send notification email to admin (optional)
        try:
            send_mail(
                'New Registration Request - Suicide Metrics',
                f'A new user {user.get_full_name()} ({user.user_type}) has registered and is awaiting approval.',
                settings.DEFAULT_FROM_EMAIL,
                [admin[0] for admin in settings.ADMINS],
                fail_silently=True,
            )
        except Exception:
            pass  # Email failure shouldn't break registration
        
        response_data = {
            'message': 'Registration submitted successfully. Please wait for admin approval.',
            'user_id': user.id,
            'status': 'pending_approval'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_registration_status(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        registration_request = RegistrationRequest.objects.get(user=user)
        
        return Response({
            'status': registration_request.status,
            'submitted_at': registration_request.submitted_at,
            'reviewed_at': registration_request.reviewed_at,
            'is_approved': user.is_approved,
            'is_active': user.is_active,
        })
    except (CustomUser.DoesNotExist, RegistrationRequest.DoesNotExist):
        return Response({'error': 'Registration not found'}, status=status.HTTP_404_NOT_FOUND)