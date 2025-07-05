from django.urls import path
from user_auths import views
 
app_name = "user_auths" 

urlpatterns = [
    
    path("register/", views.RegisterView, name="register"),
    path("login/", views.LoginView, name="login"),
    path("logout/", views.LogoutView, name="logout"),
 
]
