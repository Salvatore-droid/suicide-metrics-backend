from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, RegistrationRequest


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    user_type = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')

        if email and password:
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError('Invalid email or password')

            if not user.check_password(password):
                raise serializers.ValidationError('Invalid email or password')

            if user.user_type != user_type:
                raise serializers.ValidationError('Invalid user type for this account')

            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')

            data['user'] = user
            return data
        else:
            raise serializers.ValidationError('Must include "email" and "password"')


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'password', 'confirm_password', 
            'first_name', 'last_name', 'user_type', 'phone_number',
            'staff_id', 'department', 'role'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password fields didn't match."})
        
        # Validate email domain
        email = attrs.get('email', '')
        if not (email.endswith('@rongo.ac.ke') or email.endswith('@gmail.com')):
            raise serializers.ValidationError(
                {"email": "Please use university email (@rongo.ac.ke) or approved domain."}
            )
        
        # Validate staff ID uniqueness
        staff_id = attrs.get('staff_id')
        if staff_id and CustomUser.objects.filter(staff_id=staff_id).exists():
            raise serializers.ValidationError(
                {"staff_id": "This staff ID is already registered."}
            )
        
        # Validate email uniqueness
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "This email is already registered."}
            )
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        # Split full name into first and last name
        full_name = validated_data.pop('first_name', '').split(' ', 1)
        if len(full_name) > 1:
            validated_data['first_name'] = full_name[0]
            validated_data['last_name'] = full_name[1]
        else:
            validated_data['first_name'] = full_name[0]
            validated_data['last_name'] = ''
        
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.is_active = False  # User needs admin approval
        user.save()
        
        # Create registration request
        RegistrationRequest.objects.create(user=user)
        
        return user