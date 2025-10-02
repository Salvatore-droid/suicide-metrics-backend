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
from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone
from datetime import timedelta
import secrets
from .models import UserSession

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    print("=" * 50)
    print("🔐 LOGIN REQUEST RECEIVED")
    print("=" * 50)
    
    print(f"📦 Raw request body: {request.body}")
    
    try:
        request_data = json.loads(request.body)
        print(f"📋 Parsed login data: {json.dumps(request_data, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = LoginSerializer(data=request_data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        print(f"✅ Login successful for user: {user.email}")
        
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
            'department': user.department,
            'role': user.role,
        }
        
        response_data = {
            'message': 'Login successful',
            'user': user_data,
            'token': token,
            'expires_at': expires_at.isoformat(),
        }
        
        print(f"✅ Sending login response: {json.dumps(response_data, indent=2)}")
        return Response(response_data, status=status.HTTP_200_OK)
    
    print(f"❌ Login validation errors: {serializer.errors}")
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

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import json

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def register_view(request):
    print("=" * 50)
    print("📥 REGISTRATION REQUEST RECEIVED")
    print("=" * 50)
    
    # Print raw request data
    print(f"📦 Raw request body: {request.body}")
    
    try:
        # Try to parse JSON data
        request_data = json.loads(request.body)
        print(f"📋 Parsed JSON data: {json.dumps(request_data, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = RegistrationSerializer(data=request_data)
    
    if serializer.is_valid():
        user = serializer.save()
        print(f"✅ USER CREATED SUCCESSFULLY:")
        print(f"   - ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - Name: {user.first_name} {user.last_name}")
        
        response_data = {
            'message': 'Registration submitted successfully. Please wait for admin approval.',
            'user_id': user.id,
            'status': 'pending_approval'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    print("❌ VALIDATION ERRORS:")
    print(json.dumps(serializer.errors, indent=2))
    
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