from collections.abc import Callable, Iterable, Mapping
from typing import Any
from django.shortcuts import render, redirect
from django.views import View
import json 
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from .utils import account_activation_token
from django.urls import reverse
from django.contrib import auth
from validate_email import validate_email
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import threading

# Create your views here for handling authentication

# Email sent using threads to speed up this process
class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently = False)

# To check validity of email entered by user
class EmailValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        if not validate_email(email):
            return JsonResponse({'email_error': 'Email is invalid'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'sorry email in use,choose another one '}, status=409)
        return JsonResponse({'email_valid': True})

# To check validity of username entered by user(should contain alphanumeric characters only)
class UsernameValidationView(View):
    def post(self, request):
        data = json.loads(request.body) 
        username = data['username']

        if not str(username).isalnum():
            return JsonResponse({'username_error': 'username should only contain alphanumeric characters'}, status = 400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'sorry username in use,choose another one '}, status=409)
        return JsonResponse({'username_valid': True})
    
# For registering user(using username, email, password)
class RegistrationView(View):

    # handles GET requests to the registration page and it renders register.html which consist of form to be filled by user for registration
    def get(self, request):
        return render(request, 'authentication/register.html')
    
    # handles POST requests, which typically occur when a user submits a form
    def post(self, request):
        # Steps followed are:
        # Get user data as input
        # Validate
        # Create a user account

        # retrieves the user's input (username, email, and password) from the POST data of the request.
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        # The context dictionary in this code is like a little package of information (data entered by user), 
        # that the website sends back to the page with the form, if there is an error to refill the info already typed by user.
        context = {
            'fieldValues': request.POST
        }

        # Checks if the provided username and email do not already exist in the database. 
        # If they don't exist and the password meets a minimum length requirement, registraion process continues.
        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password) < 6:
                    messages.error(request, 'Password too short')
                    return render(request, 'authentication/register.html', context)

                #new User object is created with the provided username, password and email. 
                #user account is set to inactive (user.is_active = False). 
                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.is_active = False
                user.save()
                
                # function that retrieves information about the current website, includes details like the domain name. 
                # This information is crucial because the activation link in the email needs to point to the correct domain.
                current_site = get_current_site(request)


                email_body = {
                    'user': user,

                    # domain name of the current website.
                    'domain': current_site.domain,

                    # This is a unique identifier for the user, encoded in a way that can be safely included in a URL. 
                    # It's created by encoding the user's primary key.
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),

                    # This is a token used for account activation, generated using a function called make_token provided by account_activation_token.
                    # This token is a way of confirming that the person clicking the activation link is the same person who signed up.
                    'token': account_activation_token.make_token(user), 
                }

                # creates the actual activation link by using the reverse function which will be included in email sent to user
                link = reverse('activate', kwargs={'uidb64': email_body['uid'], 'token': email_body['token']})

                email_subject = 'Activate your account'

                activate_url = 'http://'+current_site.domain+link

                email = EmailMessage(
                    email_subject,
                    'Hi '+user.username + ', Please use the link below to activate your account \n'+activate_url,
                    'noreply@semycolon.com',
                    [email],
                )
                email.send(fail_silently=False)
                messages.success(request, 'Account successfully created')
                return render(request, 'authentication/register.html')

        return render(request, 'authentication/register.html')

 
class VerificationView(View):

    # designed to handle GET requests related to user account verification  
    def get(self, request, uidb64, token):

        # attempting to decode the uidb64 parameter, which is then used to retrieve the corresponding User object from the database
        try:
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=id)

            # It checks if the provided activation token is valid for the given user
            if not account_activation_token.check_token(user, token):
                return redirect('login'+'?message='+'User already activated')

            # If the user is already active (meaning their account has already been activated), it redirects them to the login page.
            if user.is_active:
                return redirect('login')
            user.is_active = True
            user.save()

            messages.success(request, 'Account activated successfully')
            return redirect('login')

        except Exception as ex:
            pass

        return redirect('login')

class LoginView(View):

    # handles GET requests to the login page which renders the 'login.html' template containing a login form.
    def get(self, request):
        return render(request, 'authentication/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        # checks if both the username and password are provided
        if username and password:
            user = auth.authenticate(username=username, password=password)

            # If authentication is successful and the user is active, it logs the user in using auth.login 
            if user:
                if user.is_active:
                    auth.login(request, user)
                    messages.success(request, 'Welcome, ' +user.username+' you are now logged in')
                    return redirect('expenses')
                
                # If user has not activated using activation link
                messages.error(
                    request, 'Account is not active,please check your email')
                return render(request, 'authentication/login.html')
            
            # If the authentication fails (invalid username or password)
            messages.error(
                request, 'Invalid credentials,try again')
            return render(request, 'authentication/login.html')

        messages.error(
            request, 'Please fill all fields')
        return render(request, 'authentication/login.html')

# handles logout request
class LogoutView(View):
    def post(self, request):
        auth.logout(request)
        messages.success(request, 'You have been logged out')
        return redirect('login')

class RequestPasswordResetEmail(View):
    def get(self, request):
        return render(request, 'authentication/reset-password.html') 
    
    
    def post(self, request):

        # retrieves the entered email from the form and creates a context dictionary containing the form values
        email = request.POST['email']

        context = {
            'values':request.POST
        }

        # checks if the entered email is valid using a validate_email function
        if not validate_email(email):
            messages.error(request, 'Please enter a valid email.')
            return render(request, 'authentication/reset-password.html', context)  
        
        current_site = get_current_site(request)
        
        user = User.objects.filter(email=email)

        # If the user exists, it prepares a dictionary email_contents containing user information, domain, and a token for password reset.
        if user.exists():
            email_contents = {
                    'user': user[0],
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user[0].pk)),
                    'token': PasswordResetTokenGenerator().make_token(user[0]),
                }

            # generates the reset link using the reverse function
            link = reverse('reset-user-password', kwargs={'uidb64': email_contents['uid'], 'token': email_contents['token']})

            email_subject = 'Password reset link'

            reset_url = 'http://'+current_site.domain+link

            email = EmailMessage(
                    email_subject,
                    'Hi ' + ', Please use the link below to reset your passeord \n'+reset_url,
                    'noreply@semycolon.com',
                    [email],
            )
            EmailThread(email).start()

        messages.success(request, 'We have sent you an email to reset your password.')

        
        return render(request, 'authentication/reset-password.html')   

# handle the completion of the password reset process
class CompletePasswordReset(View):
    def get(self, request, uidb64, token):

        context = {
            'uidb64': uidb64,
            'token': token
        }

        # It retrieves the user information from the provided UID and token. 
        # If the token is not valid, it adds an error message, renders the 'set-new-password.html' template, and returns.
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk = user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.success(request, 'Password reset link is invalid, please request a new link')
                return render(request, 'authentication/set-new-password.html', context)
        
        except Exception as identifier:
            pass

        return render(request, 'authentication/set-new-password.html', context)
    
    # retrieves the new password and its confirmation from the form
    def post(self, request, uidb64, token):

        context = {
            'uidb64': uidb64,
            'token': token
        }

        password = request.POST['password']
        password2 = request.POST['password2']

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'authentication/set-new-password.html', context)
        
        if len(password) < 6:
            messages.error(request, 'Password too short')
            return render(request, 'authentication/set-new-password.html', context)

        # sets the new password for the user, saves the user object, adds a success message, and redirects the user to the login page.
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk = user_id)
            user.set_password(password)
            user.save()

            messages.success(request, 'Password reset successfull')
            return redirect('login')
        
        except Exception as identifier:
            messages.info(request, 'Something went wrong, try again.')
            return render(request, 'authentication/set-new-password.html', context)