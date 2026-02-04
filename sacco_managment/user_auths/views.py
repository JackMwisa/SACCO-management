from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from user_auths.models import User
from user_auths.forms import UserRegisterForm
from core.utils.rate_limit import ratelimit
from account.models import LoginHistory


@ratelimit(max_requests=3, window_seconds=300)  # 3 registrations per 5 minutes
def RegisterView(request):
    if request.user.is_authenticated:
        messages.warning(request, f"You are already logged in.")
        return redirect("account:account")
    
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # form.save()
            new_user = form.save() # new_user.email
            username = form.cleaned_data.get("username")
            # username = request.POST.get("username")
            messages.success(request, f"Hey {username}, your account was created successfully.")
            # new_user = authenticate(username=form.cleaned_data.get('email'))
            new_user = authenticate(username=form.cleaned_data['email'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect("account:account")

    else:
        form = UserRegisterForm()
    context = {
        "form": form
    }
    return render(request, "user_auths/register.html", context)


@ratelimit(max_requests=5, window_seconds=60)  # 5 attempts per minute
def LoginView(request):
    # Check if already logged in first
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in")
        return redirect("account:account")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.warning(request, "Please provide both email and password")
            return redirect("user_auths:login")

        try:
            # Check if user exists
            user = User.objects.get(email=email)
            # Authenticate with credentials
            user = authenticate(request, email=email, password=password)

            # Get IP address for logging
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

            if user is not None:
                login(request, user)
                # Log successful login
                LoginHistory.objects.create(
                    user=user,
                    action='LOGIN',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    successful=True
                )
                messages.success(request, "You are logged in.")
                return redirect("account:account")
            else:
                # Log failed login attempt
                LoginHistory.objects.create(
                    user=User.objects.filter(email=email).first(),
                    action='LOGIN_FAILED',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    successful=False,
                    details="Invalid password"
                )
                messages.warning(request, "Invalid email or password")
                return redirect("user_auths:login")
        except User.DoesNotExist:
            # Log failed login for non-existent user
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
            LoginHistory.objects.create(
                user=None,
                action='LOGIN_FAILED',
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                successful=False,
                details="User not found"
            )
            messages.warning(request, "Invalid email or password")
            return redirect("user_auths:login")

    return render(request, "user_auths/login.html")

def LogoutView(request):
    # Log the logout action before logging out
    if request.user.is_authenticated:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')

        LoginHistory.objects.create(
            user=request.user,
            action='LOGOUT',
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            successful=True
        )

    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("user_auths:login")


def LogoutViewAdmin(request):
    # Log the logout action before logging out
    if request.user.is_authenticated:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')

        LoginHistory.objects.create(
            user=request.user,
            action='LOGOUT',
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            successful=True,
            details="Admin logout"
        )

    logout(request)
    messages.success(request, "You have been logged out from the admin.")
    return redirect("/admin/login/")