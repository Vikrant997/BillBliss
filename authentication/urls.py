from .views import RegistrationView, UsernameValidationView, EmailValidationView, VerificationView, LoginView, LogoutView, RequestPasswordResetEmail, CompletePasswordReset
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

# configuration file for mapping URLs(mentioned in html files) to views in view.py

# determine how URLs are interpreted and which view functions or classes should handle specific requests
urlpatterns = [
    path('register', RegistrationView.as_view(), name = "register"),
    path('validate-username', csrf_exempt(UsernameValidationView.as_view()), name = "validate-username"),
    path('validate-email', csrf_exempt(EmailValidationView.as_view()), name = "validate-email"),
    path('activate/<uidb64>/<token>', VerificationView.as_view(), name='activate'),
    path('login', LoginView.as_view(), name="login"),
    path('logout', LogoutView.as_view(), name="logout"),
    path('request-reset-link', RequestPasswordResetEmail.as_view(),name= "request-password"),
    path('set-new-password/<uidb64>/<token>', CompletePasswordReset.as_view(), name="reset-user-password")
]

# CSRF protection is a security feature that helps prevent unauthorized requests from being made on behalf of a user.

# In Django, when you submit a form (including a login form) on a website, 
# the framework includes a hidden CSRF token with the form data. 
# This token is used to verify that the form submission comes from the same site and isn't a malicious cross-site request.