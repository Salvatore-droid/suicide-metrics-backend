from django.urls import path
from . import views

urlpatterns = [
    path('api/login/', views.login_view, name='login'),
    path('api/logout/', views.logout_view, name='logout'),
    path('api/forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('api/register/', views.register_view, name='register'),
    path('api/registration-status/<int:user_id>/', views.check_registration_status, name='registration_status'),
]