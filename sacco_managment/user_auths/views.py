from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from user_auths.models import User
from user_auths.forms import UserRegisterForm

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

            if user is not None:
                login(request, user)
                messages.success(request, "You are logged in.")
                return redirect("account:account")
            else:
                # Generic message to prevent user enumeration
                messages.warning(request, "Invalid email or password")
                return redirect("user_auths:login")
        except User.DoesNotExist:
            # Use same generic message to prevent user enumeration
            messages.warning(request, "Invalid email or password")
            return redirect("user_auths:login")

    return render(request, "user_auths/login.html")

def LogoutView(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("user_auths:login")


def LogoutViewAdmin(request):
    logout(request)
    messages.success(request, "You have been logged out from the admin.")
    return redirect("/admin/login/")  # or redirect wherever you want